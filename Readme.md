# Milter Attachments Scan Project Setup Guide

## Prerequisites

- Python 3
- Postfix installed
- Access to a terminal with superuser privileges

## 1. Install Postfix

First, install Postfix if it's not already installed. On a Debian-based system, use:

```bash
sudo apt install postfix
```

## 1.1. Configure Postfix to Enable Milter Support

Edit the Postfix configuration file (`/etc/postfix/main.cf`) to enable Milter support by adding the following lines:

```text
smtpd_milters = inet:localhost:9900
non_smtpd_milters = $smtpd_milters
milter_default_action = accept
milter_protocol = 6
```

Save the file and restart Postfix to apply the changes:

```bash
sudo systemctl restart postfix
```

## 2. Install PyMilter

You can install PyMilter directly from the repository:

[PyMilter GitHub Repository](https://github.com/sdgathman/pymilter?tab=readme-ov-file)

Or, you can install the necessary dependencies using the package manager:

```bash
sudo apt install libmilter-dev
sudo apt install python3-milter
```

## 3. Launch the Milter with Python

Navigate to the directory containing your `simple_milter.py` script and run it using Python 3:

```bash
python3 simple_milter.py
```

This will start the Milter service and listen on the configured socket (`inet:localhost:9900`).

## 4. Testing the Milter

Send an email through Postfix to see if the Milter intercepts it. You can use the `mail` command:

```bash
echo "This is the body of the email, and it contains an attachments" | mailx -s "Test Email with Attachment" -A /path/to/attachment/file your_email@localhost
```

Check the Milter logs to verify that the email was processed.

