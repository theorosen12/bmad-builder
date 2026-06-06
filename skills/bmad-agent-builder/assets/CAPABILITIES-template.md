# Capabilities

## Built-in

| Code | Name | Description | Source |
|------|------|-------------|--------|
{capabilities-table}

{if-evolvable}
## Learned

_Capabilities added by the owner over time. Prompts live in `capabilities/`._

| Code | Name | Description | Source | Added |
|------|------|-------------|--------|-------|

## How to Add a Capability

Tell me "I want you to be able to do X" and we'll create it together.
I'll write the prompt, save it to `capabilities/`, and register it here.
Next session, I'll know how.

Two references guide the work, and they stay distinct. `./references/capability-authoring.md` carries the mechanics: the frontmatter, the creation flow, and how a capability gets registered here and in INDEX.md. The quality bar lives in the prompt-quality canon, which I load at author time per my standing order. The shipped copy is `./references/prompt-quality-canon.md`, with the published canon at `{siteBase}/explanation/outcome-driven-prompt-quality/` as the fallback. Pointing out to the canon means a capability added long after install is still held to the current standard rather than the snapshot baked in at build time.
{/if-evolvable}

## Tools

Prefer crafting your own tools over depending on external ones. A script you wrote and saved is more reliable than an external API. Use the file system creatively.

### User-Provided Tools

_MCP servers, APIs, or services the owner has made available. Document them here._
