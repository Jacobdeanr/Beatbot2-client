from cli.models import Config
from service import ApiClient
from cli.views import CliView
from cli.controller import CliController

def main() -> None:
    cfg = Config(api_base="http://127.0.0.1:5000", queue_id="cli")
    api = ApiClient(cfg)
    view = CliView()
    controller = CliController(api, view)
    controller.run()

if __name__ == "__main__":
    main()