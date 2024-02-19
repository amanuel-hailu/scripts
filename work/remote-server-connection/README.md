# SSH Auto Login Script

This script, `ssh_auto_login.exp`, is used to automate SSH login using 1Password for password management. It uses the 'expect' command to automate interactions with the SSH login process.

## Requirements

- Expect: A command-line tool for automating interactive applications such as telnet, ftp, passwd, fsck, rlogin, tip, etc.
- 1Password CLI: A command-line tool that provides a way to interact with 1Password accounts.

## Usage

The script accepts two arguments:

1. The 1Password key reference for the SSH password (e.g., "op://Work Account/SSH RUMBA UTIL/password")
2. The SSH host name as defined in the SSH config file (e.g., "rumbautil")

To run this script, use the following command:

**./ssh_auto_login.exp** **"op://Work Account/SSH RUMBA UTIL/password"** **rumbautil**

## How It Works

- The first argument is assigned to the `pass_reference` variable.
- The second argument is assigned to the `ssh_hostname` variable.
- The `exec` command is used to execute the `op read` command, which retrieves the password from 1Password. The retrieved password is assigned to the `password` variable.
- The `spawn` command is used to start the SSH process for the server configured in the SSH config file.
- The `expect` command waits for the password prompt.
- The `send` command provides the password when the password prompt is encountered.
- The `interact` command allows the user to interact with the spawned process after the script has run.

## Note

Ensure that the 1Password CLI is installed and configured correctly on your system. Also, make sure that the SSH host is correctly configured in your SSH config file.
