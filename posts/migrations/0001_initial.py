import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("palshare", "0003_message_deleted_at_message_edited_at_reaction"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="Post",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("text", models.TextField()),
                        (
                            "followers_only",
                            models.BooleanField(default=False),
                        ),
                        (
                            "created_at",
                            models.DateTimeField(auto_now_add=True),
                        ),
                        (
                            "updated_at",
                            models.DateTimeField(auto_now=True),
                        ),
                        (
                            "like_count",
                            models.PositiveIntegerField(default=0),
                        ),
                        (
                            "comment_count",
                            models.PositiveIntegerField(default=0),
                        ),
                        (
                            "share_count",
                            models.PositiveIntegerField(default=0),
                        ),
                        (
                            "author",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="posts",
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                    ],
                    options={
                        "ordering": ["-created_at"],
                    },
                ),
                migrations.CreateModel(
                    name="Media",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        (
                            "file",
                            models.FileField(
                                upload_to="posts/%Y/%m/"
                            ),
                        ),
                        (
                            "kind",
                            models.CharField(
                                choices=[
                                    ("image", "Image"),
                                    ("video", "Video"),
                                ],
                                default="image",
                                max_length=5,
                            ),
                        ),
                        (
                            "alt",
                            models.CharField(
                                blank=True,
                                max_length=200,
                            ),
                        ),
                        (
                            "post",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="media",
                                to="posts.post",
                            ),
                        ),
                    ],
                ),
                migrations.CreateModel(
                    name="Comment",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("text", models.TextField()),
                        (
                            "created_at",
                            models.DateTimeField(auto_now_add=True),
                        ),
                        (
                            "like_count",
                            models.PositiveIntegerField(default=0),
                        ),
                        (
                            "author",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="comments",
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                        (
                            "parent",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="replies",
                                to="posts.comment",
                            ),
                        ),
                        (
                            "post",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="comments",
                                to="posts.post",
                            ),
                        ),
                    ],
                    options={
                        "ordering": ["created_at"],
                    },
                ),
            ],

            database_operations=[
                migrations.RunSQL(
                    sql='ALTER TABLE "palshare_post" RENAME TO "posts_post";',
                    reverse_sql='ALTER TABLE "posts_post" RENAME TO "palshare_post";',
                ),
                migrations.RunSQL(
                    sql='ALTER TABLE "palshare_media" RENAME TO "posts_media";',
                    reverse_sql='ALTER TABLE "posts_media" RENAME TO "palshare_media";',
                ),
                migrations.RunSQL(
                    sql='ALTER TABLE "palshare_comment" RENAME TO "posts_comment";',
                    reverse_sql='ALTER TABLE "posts_comment" RENAME TO "palshare_comment";',
                ),
            ],
        ),
    ]
