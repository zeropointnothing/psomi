"""
PSOMI Commands

Organized into separate cogs.
"""
import pkgutil

command_groups = []
for package in pkgutil.iter_modules([__path__][0]):
    command_groups.append("psomi.commands."+package.name)

__all__ = ["command_groups"]
