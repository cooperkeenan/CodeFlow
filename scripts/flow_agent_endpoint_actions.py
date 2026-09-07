from browser_driver.flow_reports import (
    print_endpoint_detail,
    print_method_code,
    print_sidebar,
)
from browser_driver.flow_session import FlowSession
from repo_home_fixture import endpoint_slug

USAGE = """  endpoint:<entry_id>  click that endpoint link on the repo home page, open the endpoint page
  detail               print the endpoint page: method, path, title, description, contract
                        param/response counts, generated note, and key-method names
  method:<fqn>         click that key-method row, assert its code pane is non-empty
  back                 go back from method code to the key-method list
  diagram              press "view diagram" and wait for the canvas
  sidebar              print every row of the /flow endpoint sidebar with its active flag
"""


def run_endpoint_action(session: FlowSession, verb: str, arg: str) -> bool:
    if verb == "endpoint":
        session.open_endpoint(endpoint_slug(arg))
        print(f"opened endpoint page for {arg}")
    elif verb == "detail":
        print_endpoint_detail(session)
    elif verb == "method":
        session.open_method(arg)
        print_method_code(session)
    elif verb == "back":
        session.method_back()
        print("back to method list")
    elif verb == "diagram":
        session.open_diagram()
        print("opened diagram")
    elif verb == "sidebar":
        print_sidebar(session)
    else:
        return False
    return True
