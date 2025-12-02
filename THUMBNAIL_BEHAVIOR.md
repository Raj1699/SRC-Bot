# Thumbnail Behavior on Private Posts

This document explains how thumbnails are handled when processing private posts (`t.me/c/...`).

## Logic Overview

When the bot processes a message from a private channel:

1. **Custom Thumbnail Priority**:
   - The bot first checks if the user has set a custom thumbnail using the `/settings` -> `Set Thumbnail` command.
   - If a custom thumbnail exists for the user, it is **always** used for both videos and documents.

2. **Video Files (if no custom thumbnail)**:
   - If the user has **not** set a custom thumbnail, the bot generates a new thumbnail.
   - It takes a screenshot from the video at 50% of its duration.
   - The **original thumbnail** from the source message is **discarded/replaced** by this generated screenshot.

3. **Document Files (if no custom thumbnail)**:
   - If the user has **not** set a custom thumbnail, `thumb_path` is set to `None`.
   - The document is uploaded without an explicit thumbnail provided by the bot.
   - The **original thumbnail** from the source message is **discarded**.

## Summary

**Is the thumbnail on a private post removed?**
**Yes.** The original thumbnail from the source message is not preserved. It is replaced by either:
1. The user's custom thumbnail (if set).
2. A newly generated screenshot (for videos).
3. Nothing (for documents, if no custom thumb).
