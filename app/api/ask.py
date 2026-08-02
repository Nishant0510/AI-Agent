# app/api/ask.py (excerpt)
from app.services.logging_service import RequestLogContext
from app.agent.graph.callbacks import PipelineLoggingCallback

import traceback
@router.post("/ask")
async def ask(request: AskRequest):
    log_ctx = RequestLogContext(question=request.question)
    callback = PipelineLoggingCallback(log_ctx)

    try:
        final_state = await agent_graph.ainvoke(
            {"question": request.question},
            config={"callbacks": [callback]},
        )

    except Exception as e:
        traceback.print_exc()          # prints complete stack trace
        print("ERROR:", repr(e))

        log_ctx.error = str(e)
        log_ctx.finalize({"question": request.question})

        raise

    log_ctx.finalize(final_state)
    return final_state.get("final_response")