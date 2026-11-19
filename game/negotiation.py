"""Weight a feasible counterproposal at the responder's decision point."""
def choose_reply(ctx, slot, base, other="same"):
    if not 0 <= base <= 1:
        raise ValueError("反提案的基准权重无效。")
    return ctx.choice(slot, {
        "counter": base * ctx.params["counteroffer_weight"],
        other: 1 - base,
    })
