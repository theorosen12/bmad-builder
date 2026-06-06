<!-- Shipped copy. Canonical master: _bmad-output/prompt-quality-canon.md. Sync from there, never edit here. -->
# Outcome-Driven Prompt Quality

The canon for what earns its place in anything you build with a prompt, whether that is a single capability or a whole flow. The same tests apply everywhere, because every line you write competes with the version of itself that was never written.

## The core test

For every line, ask whether a capable model would do this correctly without being told. If yes, cut it. A line earns its place only by preventing a failure that would otherwise happen, so it must beat its own absence. If you cannot name something the line produces that its absence would not, the line is friction and it goes.

## The two-version comparison

You cannot judge structure from inside a single run, because the output looks the same whether the model did its best work or settled for less. Step outside the run and compare. Write the smallest version of what you are building, around five lines, holding only the role, the outcome, the consumer of that outcome, and any rule serious enough that you can point to the damage its absence has caused. Then run the small version and the elaborate one on the same input and read the verdict.

| What you see | What it means |
|---|---|
| Small one wins | The structure was a straitjacket. Cut it. |
| They tie | The structure is decoration. Defend each line or kill it. |
| Small one rougher but recoverable in a couple of turns | You bought convenience, not quality. Allowed, if you are honest about it. |
| Small one materially worse and stays worse | The structure earned its keep, for now. |

## The deeper floor and when to retire

Below your small version sits the bare model with nothing wrapped around it, and that floor rises with every model release. What survives is the work the model cannot do for itself: resolving file paths, holding downstream contracts, wiring together systems that do not know about each other, and carrying institutional knowledge that lives nowhere but your team. Test against the bare model on every release, and when a capability stops beating it, retire that capability rather than patching it, because the model has caught up to the work it was doing.

## Write what survives as a goal

Cutting structure that does not earn its place is only half the work, because what survives can still box the model in for no reason. Phrase what remains as intent and let the model find the path. Reserve exact procedure for the few fragile operations where a wrong move actually costs something, such as a precise script invocation or an API call with consequences. Apply the order test to any numbered sequence: if no step depends on a prior step's output, the numbering is decoration and it collapses to one goal sentence.

## Progressive disclosure

Keep the entry file scannable, since it is what loads every time and sets the cost of every turn. Carve content into separate references only when the entry file grows too big to read at a glance, and when you do, each carved file has to stand on its own because the entry context can drop mid-flow. Stay one level deep, so the entry routes to a reference and never a reference to another reference.

## Cheaper signals

These hold one variable steady, change another, and watch the output. Run the same input five times: nearly identical results mean you over-determined the work and left no room to think, while wildly varying results mean you under-specified something you can now go find. Run very different inputs through the same prompt: if they all come back looking alike, your template has gotten louder than the input. Watch the trajectory of rigid compliance too, because a model marching through numbered steps in order rather than adapting them is a sign the structure is constraining it.

## The habit

None of this needs an eval suite. For each section of what you build, ask the single outcome you want from it, then ask what the model already knows how to do there, which is usually most of it, and then ask what it genuinely needs from you that it cannot infer, meaning the wiring and the schemas and the rules with real consequences behind them. Whatever remains is structure you are imposing, and you owe yourself a clear account of what it buys. If you cannot name that, it is over-structure.
