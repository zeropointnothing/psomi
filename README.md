# PSOMI.v2 (ZRpB)

An open-source Proxy bot designed for Role-Playing.


## Why PSOMI.v2?

Discord has plenty of Role-Playing focused proxy bots, but PSOMI.v2 aims to be more than just another. Here's what it has to offer!

### Stronger, Smarter, Better!

PSOMI is being rewritten from the ground up, making v2 better in every way! PSOMI.v2 can parse, respond, and edit faster than ever before, all powered by wonderful SQL!

### Modern and Sleek

Unlike v1 and most proxy bots, which rely specifically on "prefix commands", PSOMI.v2 has been rewritten with modern Discord features such as Slash Commands, embeds, and buttons!

Additionally, supported commands have access to nifty features such as Auto-complete and predetermined options that'll make using PSOMI that much easier!

### Open-Source

PSOMI.v2 will always keep its code open, making it easier to find and squash bugs, add features, and host your own instance!

Not only that, but PSOMI.v2's code has been designed with **simplicity** and **expandability** in mind. If you don't like something, change it! With a class-based approach, and plenty of documentation built into the codebase, PSOMI.v2 will do its best to help!

### Preferences Galore!

_(coming soon!)_

PSOMI.v2 is being re-designed around _you_ (or your users!), allowing almost every aspect of your Proxy experience to be changed and modified to your liking!

---

### And So Much More!

PSOMI.v2 isn't done yet, and will continue to grow when it is! View the [Roadmap](https://github.com/users/zeropointnothing/projects/14) to see what's done, what's being done, and what's planned for the future!


## Why (not) PSOMI.v2?

PSOMI.v2 is still in a very early state. This means bugs or breaking changes could happen at any time!

The rewrite may be practically finished, but PSOMI.v2's journey is not!

## Hosting Your Own Instance

To host your own instance, you need three things:

1. A computer to host it on
2. A Discord Bot Token
3. Python 3.13

Then, follow these steps!

**First, clone the repository:**

```bash
git clone https://github.com/zeropointnothing/psomi
```

**Then, once inside the `psomi` folder, install the required dependencies inside a virtual environment:**

```bash
python -m venv .venv
# On Windows systems (PowerShell)
.venv/Scripts/Activate.ps1
# And CMD (batch)...
.venv/Scripts/activate.bat

# On Linux Systems (fish)
source .venv/bin/activate.fish
# Plain Bash...
source .venv/bin/activate

# Note, that you may have to remove the audioop-lts package if your installation already has audioop present.
pip install -r requirements.txt 
```

**Finally, create the config!**

_inside a file named `config.json`:
```json
{
    "token": "your.bots_token_here",
    "db": "database.db"
}
```

**...and run PSOMI.v2!**

```bash
python -m psomi
```
