from terdo.main import Terdo


async def test_app_close():
    """Test the app exists when pressing the "q" key."""
    app = Terdo()

    async with app.run_test() as pilot:
        await pilot.press("q")

        # If the app is not exited the return_code should be None, after
        # succesfull exit it should be 0
        assert pilot.app.return_code == 0
