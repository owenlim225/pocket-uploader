# Pocket Uploader

Run the uploader in VS Code on Windows with your unlocked Samsung connected by USB.
The video data stays on the phone and the signed-in YouTube app performs the upload.

## One-time setup

1. Install Python 3.10 or newer, the VS Code Python and Python Debugger extensions, and [Android SDK Platform-Tools](https://developer.android.com/tools/releases/platform-tools). Add the extracted platform-tools directory to your Windows PATH or install it in the default Android SDK location.
2. Open this folder in VS Code. In its terminal run `python -m pip install -r requirements.txt`. Select that Python interpreter in VS Code.
3. On the phone, enable Developer options by tapping **Settings → About phone → Software information → Build number** seven times. Enable **USB debugging**, connect using a data cable, unlock the phone, and accept the computer's debugging prompt.
4. Open YouTube and select the intended channel. Enable YouTube notifications for upload confirmation. Use English for YouTube and My Files. Leave the phone unlocked and available while uploading.

## Run

Open Run and Debug and select **Preview titles**. Compare the list with **My Files → Videos**. Discovery uses Android's shared video index, so entries can differ from the Samsung category on some devices. Preview does not reserve titles or upload files.

Open the My Files home screen, select **Run uploader** in VS Code, and press F5. The program opens Videos and shares each indexed video's Android media URI directly with YouTube. The first run treats listed files as new. Use the same YouTube channel on subsequent runs. Progress is stored under `%LOCALAPPDATA%\PocketUploader`.

A filename such as `20261107_222117.mp4` becomes **November 7, 2026**. Multiple clips for a date get **PART 1**, **PART 2**, and so on, earliest first. Later runs keep allocated numbers and append new clips. Other filenames supply the title without the extension.

If the app layout, visibility selection, or audience setting cannot be verified, the program pauses. Reopen the My Files home screen before restarting. If YouTube reports a limit, resume when the channel can upload again.

## Interrupted or unconfirmed uploads

Run `python uploader.py preview` to see entry IDs. A **review** entry means submission may have happened. Check the intended channel in YouTube Studio. If the video is still uploading or processing, wait for its outcome.

- After verifying success, run `python uploader.py resolve 12 done`, substituting the entry ID.
- After verifying the upload did not succeed, run `python uploader.py resolve 12 retry`.

Run the uploader again to continue. Completion detection requires a new YouTube notification containing the exact title and an English completion message. App versions with other notification formats require manual review. A new phone, a moved or modified file, or deleting the database can cause a previously uploaded clip to appear new.
