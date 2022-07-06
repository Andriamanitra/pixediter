from hecate.hecate import Runner


def test_application_runs():
    with Runner("pixediter") as h:
        h.await_text("PixEdiTer")
        h.press(":h")
        h.press("Enter")
        h.await_text("Press any key to continue")
        h.press("q")
        h.await_exit()
