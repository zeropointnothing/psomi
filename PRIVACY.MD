# PSOMI Privacy Policy

## Introduction
PSOMI is a decentralized bot system designed to facilitate character-based interactions using webhooks. Each instance operates independently, meaning individual instance owners are responsible for managing their own privacy policies. However, this document outlines the recommended privacy practices that should be followed to ensure transparency and user security.

## Data Stored by PSOMI
Each PSOMI instance **will store** the following data to enable functionality:
- **User-submitted data**, including:
  - Character names, ProxyGroup names, and submitted avatar URLs.
- **Discord User IDs**, required for access control and Character Lookup:
  - This ensures only the user and any explicitly authorized individuals can view, modify, or delete their characters.
- **Message IDs**, necessary for persistent ownership tracking of proxied messages:
  - These allow users to edit or delete their webhook-based messages.
  - Old records are **automatically purged** based on the instance owner's configured retention period and message limit.

## Data **NOT** Stored by PSOMI
- **Message Content**
  - Beyond temporary processing, message content is **NEVER** saved to persistent storage to protect user privacy.

## Data Access & Permissions
A PSOMI instance **CAN**:
- View **any message it has read access to**, as required for parsing character-based interactions.
- View, modify, or delete any persistent character data submitted to the bot.

A PSOMI instance **CAN NOT**:
- Collect **background information** on a user and use it for any purpose.

## Instance Owner Responsibilities
Since PSOMI operates on a decentralized model, instance owners are responsible for managing their own deployments. While this privacy policy provides a recommended guideline, individual instances may modify their policies. **Any modifications must be openly shared with instance users** to ensure transparency.

## Privacy Policy Updates
This privacy policy may be updated to reflect improvements or changes in PSOMI’s functionality. Instance owners who modify this policy **must** clearly disclose their version to their users.

## Questions or Concerns
For concerns regarding a specific PSOMI instance, users should contact the respective instance owner.

