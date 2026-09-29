"""Tests migrated from palshare/test_interactions.py."""

"""The seven controls that used to render and do nothing.

Each one is a form now, so each one is testable the way a form is: post to it
and look at the row it was supposed to create. The pair of tests that matters
most in here is the toggle pair — press once, press again, and end up where
you started, with the counter cache still telling the truth.
"""

from django.contrib.auth import get_user_model

from django.test import TestCase

from django.urls import reverse

from accounts.models import Profile

from posts.models import Comment, Post

from interactions.models import CommentLike, Like, Share, Save

from connections.models import Follow

from messaging.models import Conversation

from interactions.services import set_like

User = get_user_model()

PASSWORD = "lab-passphrase-2026"

class InteractionTestCase(TestCase):
    def setUp(self):
        self.asha = User.objects.create_user("asha", password=PASSWORD, first_name="Asha")
        self.bello = User.objects.create_user("bello", password=PASSWORD, first_name="Bello")
        self.asha_profile = Profile.objects.get(user=self.asha)
        self.bello_profile = Profile.objects.get(user=self.bello)
        self.post = Post.objects.create(author=self.asha, text="press things on me")
        self.comment = Comment.objects.create(post=self.post, author=self.asha, text="a comment")
        self.client.login(username="bello", password=PASSWORD)
        self.feed = reverse("posts:feed")

    def press(self, name, args, **data):
        return self.client.post(reverse(name, args=args), {"next": self.feed, **data})

class PostActionTests(InteractionTestCase):
    def test_like_toggles_and_the_counter_follows(self):
        self.press("interactions:post-like", [self.post.pk])
        self.post.refresh_from_db()
        self.assertEqual((self.post.like_count, Like.objects.count()), (1, 1))

        self.press("interactions:post-like", [self.post.pk])
        self.post.refresh_from_db()
        self.assertEqual((self.post.like_count, Like.objects.count()), (0, 0))

    def test_a_drifted_counter_cannot_go_negative(self):
        """A PositiveIntegerField underflows to four billion, not to -1.

        Counter caches drift — that is the price of caching them — so removal
        has to cope with "the row is here but the counter already says zero".
        """
        set_like(self.bello, self.post, True)
        Post.objects.filter(pk=self.post.pk).update(like_count=0)  # drift
        set_like(self.bello, self.post, False)
        self.post.refresh_from_db()
        self.assertEqual(self.post.like_count, 0)

    def test_share_toggles(self):
        self.press("interactions:post-share", [self.post.pk])
        self.post.refresh_from_db()
        self.assertEqual((self.post.share_count, Share.objects.count()), (1, 1))
        self.press("interactions:post-share", [self.post.pk])
        self.post.refresh_from_db()
        self.assertEqual((self.post.share_count, Share.objects.count()), (0, 0))

    def test_save_toggles_and_the_saved_page_follows(self):
        self.press("interactions:post-save", [self.post.pk])
        self.assertEqual(Save.objects.count(), 1)
        self.assertContains(self.client.get(reverse("posts:saved")), "press things on me")
        self.press("interactions:post-save", [self.post.pk])
        self.assertEqual(Save.objects.count(), 0)

    def test_you_cannot_like_a_post_you_cannot_see(self):
        hidden = Post.objects.create(author=self.asha, text="hidden", followers_only=True)
        response = self.press("interactions:post-like", [hidden.pk])
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Like.objects.count(), 0)

    def test_an_action_route_refuses_a_get(self):
        """A GET that writes is a GET any <img> tag can trigger."""
        response = self.client.get(reverse("interactions:post-like", args=[self.post.pk]))
        self.assertEqual(response.status_code, 405)

    def test_next_cannot_send_you_off_site(self):
        response = self.client.post(reverse("interactions:post-like", args=[self.post.pk]),
                                    {"next": "https://evil.test/steal"})
        self.assertRedirects(response, self.feed)

    def test_the_card_has_no_inert_buttons_left(self):
        """Every control on a post card submits something.

        This used to assert `type="button"` appeared nowhere on the page, which
        worked while the app had no JavaScript at all. The emoji picker is the
        one exception and a real one: its keys type into a textarea, so they
        must not submit. The assertion moved to the card itself, which is what
        the test was ever about — the picker lives in the composer, above it.
        """
        body = self.client.get(self.feed).content.decode()
        card = body[body.index("<article class=\"post\">"):body.index("</article>")]
        self.assertNotIn('type="button"', card)
        self.assertIn(reverse("interactions:post-like", args=[self.post.pk]), body)

    def test_the_only_non_submitting_buttons_are_the_emoji_keys(self):
        """The picker is the app's one piece of JavaScript, and it is opt-in.

        `hidden` in the markup means a browser with scripting off shows no
        button at all, rather than a button that quietly does nothing — which
        is the state this whole test class exists to prevent.
        """
        body = self.client.get(self.feed).content.decode()
        self.assertEqual(body.count('type="button"'), body.count('class="emoji-key"'))
        self.assertIn('data-emoji-picker="composer-text" hidden', body)

class CommentActionTests(InteractionTestCase):
    def test_comment_like_toggles(self):
        self.press("interactions:comment-like", [self.comment.pk])
        self.comment.refresh_from_db()
        self.assertEqual((self.comment.like_count, CommentLike.objects.count()), (1, 1))
        self.press("interactions:comment-like", [self.comment.pk])
        self.comment.refresh_from_db()
        self.assertEqual((self.comment.like_count, CommentLike.objects.count()), (0, 0))

    def test_replying_sets_the_parent(self):
        self.client.post(reverse("posts:post-detail", args=[self.post.pk]),
                        {"text": "a reply", "parent": self.comment.pk})
        self.assertEqual(Comment.objects.get(text="a reply").parent_id, self.comment.pk)

    def test_a_reply_to_a_reply_flattens_to_one_level(self):
        """The model allows any depth — a CheckConstraint cannot walk a tree —
        so the rule lives in the service."""
        self.client.post(reverse("posts:post-detail", args=[self.post.pk]),
                         {"text": "a reply", "parent": self.comment.pk})
        reply = Comment.objects.get(text="a reply")
        self.client.post(reverse("posts:post-detail", args=[self.post.pk]),
                         {"text": "deeper", "parent": reply.pk})
        self.assertEqual(Comment.objects.get(text="deeper").parent_id, self.comment.pk)

    def test_you_cannot_reply_onto_another_posts_comment(self):
        other = Post.objects.create(author=self.asha, text="another post")
        response = self.client.post(reverse("posts:post-detail", args=[other.pk]),
                                    {"text": "smuggled", "parent": self.comment.pk})
        self.assertEqual(response.status_code, 404)
