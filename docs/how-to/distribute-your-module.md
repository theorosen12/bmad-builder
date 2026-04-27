---
title: 'Distribute Your Module'
description: Set up a Git repository to share your BMad module so others can install it
---

This guide walks through publishing a BMad module to a Git repository with a `.claude-plugin/marketplace.json` manifest so anyone can install it in one command.

## When to Use This

- You have a module ready to share publicly or within your organization
- Others should be able to install it via the BMad installer
- The repository may host one module or several

## When to Skip This

- The module is for personal use in a single project. Keep the skills in your project.
- The module isn't stable yet. Distribute once it is.

:::note[Prerequisites]

- A completed, validated BMad module (see **[Build Your First Module](/tutorials/build-your-first-module.md)**)
- A Git repository on any host (GitHub, GitLab, Bitbucket, or self-hosted)
- Git installed locally
:::

:::tip[Quick Path]
Start from the [BMad Module Template](https://github.com/bmad-code-org/bmad-module-template). Click **Use this template** on GitHub, add your skills under `skills/`, update `marketplace.json`, and push. If you already have a repo with skills, use Create Module (CM) to scaffold the manifest and registration files directly.
:::

## Step 1: Configure the Plugin Manifest

Modules are discovered through a `.claude-plugin/marketplace.json` manifest at the repository root. Create Module generates this file for you. Verify and complete it before publishing.

:::tip[Installer Support]
The BMad Method installer (`npx bmad-method install`) supports installing custom modules from any Git host or local path. Users can install interactively or via `--custom-source <url-or-path>`. See the [BMad Method install guide](https://docs.bmad-method.org/how-to/install-custom-modules/) for details.
:::

This format works for any skills-capable platform, not just Claude, we just utilize the claude file as a convention to support any skills based platform.

A minimal manifest for a single module:

```json
{
  "name": "my-module",
  "owner": { "name": "Your Name" },
  "license": "MIT",
  "homepage": "https://github.com/your-github/my-module",
  "repository": "https://github.com/your-github/my-module",
  "keywords": ["bmad", "your-domain"],
  "plugins": [
    {
      "name": "my-module",
      "source": "./",
      "description": "What your module does in one sentence.",
      "version": "1.0.0",
      "author": { "name": "Your Name" },
      "skills": [
        "./skills/my-agent",
        "./skills/my-workflow"
      ]
    }
  ]
}
```

| Field | Purpose |
| ----- | ------- |
| **name** | Package identifier, lowercase and hyphenated |
| **plugins[].source** | Path from repo root to the module's skill folder parent |
| **plugins[].skills** | Array of relative paths to each skill directory |
| **plugins[].version** | Semantic version; bump on each release |

For repositories that ship multiple modules, add an entry to the `plugins` array for each one, pointing to its own skill directories.

## Step 2: Structure Your Repository

Organize the repository so skills can be located relative to `marketplace.json`. The recommended layout places `module.yaml` and `module-help.csv` at the **module root**, alongside the skill folders. This is how the official BMad modules ship today.

### Single-module repository (recommended)

```
my-module/
├── .claude-plugin/
│   └── marketplace.json
├── skills/
│   ├── module.yaml             # Registration manifests at module root
│   ├── module-help.csv
│   ├── my-agent/
│   │   ├── SKILL.md
│   │   ├── prompts/
│   │   └── scripts/
│   └── my-workflow/
│       ├── SKILL.md
│       └── prompts/
├── README.md
└── LICENSE
```

In this layout, the BMad installer reads `module.yaml` and `module-help.csv` directly from the module root. No setup skill is needed; the installer handles agent registration, help registration, and any cross-project config from these two files.

### Multi-module marketplace repository

```
my-marketplace/
├── .claude-plugin/
│   └── marketplace.json          # Multiple entries in plugins[]
├── modules/
│   ├── module-a/
│   │   ├── module.yaml
│   │   ├── module-help.csv
│   │   ├── skill-one/
│   │   └── skill-two/
│   └── module-b/
│       ├── module.yaml
│       ├── module-help.csv
│       └── standalone-skill/
├── README.md
└── LICENSE
```

:::caution[Skill Paths Must Match]
The `skills` array in `marketplace.json` must match the actual directory paths relative to the repository root. If you reorganize your folders, update the manifest.
:::

### Alternative: Direct-Download Layouts

If your users install by copying the folder into their project rather than running the BMad installer, the manifests can ship inside a skill so that running the skill triggers registration. The installer also accepts these layouts as fallbacks.

**Multi-skill direct download (setup skill bundles registration):**

```
my-module/
├── .claude-plugin/
│   └── marketplace.json
├── skills/
│   ├── my-agent/
│   ├── my-workflow/
│   └── mymod-setup/             # Setup skill carries registration
│       ├── SKILL.md
│       ├── assets/
│       │   ├── module.yaml
│       │   └── module-help.csv
│       └── scripts/
│           ├── merge-config.py
│           ├── merge-help-csv.py
│           └── cleanup-legacy.py
├── README.md
└── LICENSE
```

**Single-skill direct download (skill self-registers):**

```
my-skill/
├── .claude-plugin/
│   └── marketplace.json
├── skills/
│   └── my-skill/
│       ├── SKILL.md             # Triggers registration on first run
│       ├── assets/
│       │   ├── module-setup.md
│       │   ├── module.yaml
│       │   └── module-help.csv
│       ├── references/
│       └── scripts/
│           ├── merge-config.py
│           └── merge-help-csv.py
├── README.md
└── LICENSE
```

Choose an alternative layout only when direct-download distribution is a primary requirement. The skills themselves should still be [self-runnable](/explanation/skill-authoring-best-practices.md#skills-must-be-self-runnable) regardless of how registration is handled.

## Step 3: Verify the Manifest

Before publishing, confirm the manifest is accurate.

### Check skill paths

Every path in the `skills` array must point to a directory containing a `SKILL.md` file.

### Check module registration files

For root placement (recommended): `module.yaml` and `module-help.csv` at the module root, alongside the skill folders. For direct-download layouts: in the setup skill's `assets/` (multi-skill) or in the skill's own `assets/` (standalone).

### Run Validate Module

```
"Validate my module at ./skills"
```

Validate Module (VM) checks for missing files, orphan entries, and other structural problems. Fix anything it flags before publishing.

## Step 4: Publish

Push your repository to a Git host (GitHub, GitLab, Bitbucket, or self-hosted). Once the repo is accessible, anyone with permission can install it.

### Installing your module

Users install custom modules through the BMad installer:

```bash
# Interactive: the installer prompts for a custom source URL or path
npx bmad-method install

# Non-interactive: specify the source directly
npx bmad-method install --custom-source https://github.com/your-org/my-module --tools claude-code --yes
```

The installer accepts HTTPS URLs, SSH URLs, URLs with deep paths (e.g., `/tree/main/subdir`), and local file paths.

### Private or organization modules

For private repos, users need Git access to clone. The installer uses whatever Git authentication is configured on the machine.

### Versioning

Tag releases with semantic versions. Installs pull from the default branch unless the user specifies a tag or branch.

## What You Get

After publishing, users can:

- Install via the BMad installer from any Git URL or local path; the installer reads `module.yaml` and `module-help.csv` from the module root and handles registration automatically
- Browse your module's capabilities through the help system
- Get configuration prompts defined in `module.yaml`
- For direct-download layouts: run the setup skill (or the self-registering skill with `setup`/`configure`) to register manually

## Step 5: List in the Marketplace (Optional)

Submit your module to the [BMad Plugins Marketplace](https://github.com/bmad-code-org/bmad-plugins-marketplace) for visibility alongside official modules. A listing isn't required for installation, but it adds discoverability and a trust tier badge after review.

See the marketplace [CONTRIBUTING.md](https://github.com/bmad-code-org/bmad-plugins-marketplace/blob/main/CONTRIBUTING.md) for the submission process.

## Tips

- Include a `README.md` covering what the module does, how to install it, and any external dependencies
- Add a `LICENSE` file. MIT is common for open-source BMad modules.
- Keep the `marketplace.json` version in sync with your release tags
- External dependencies (CLI tools, MCP servers) should be documented in the README and detected by the skills that need them at runtime, not solely by an installer-time check
- Run `Validate Module (VM)` before each release to catch regressions
