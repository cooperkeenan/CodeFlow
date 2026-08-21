from flow_session import FlowSession

_DOT_SELECTOR = '[title="step {index}"]'


class TourSession(FlowSession):
    def pause(self) -> None:
        self._page.click('[title="play / pause (space)"]')
        self._page.wait_for_timeout(200)

    def goto_step(self, number: int) -> None:
        self._page.click(_DOT_SELECTOR.format(index=number))
        self._page.wait_for_timeout(1100)

    def narration(self) -> dict:
        return self._page.evaluate(
            r"""() => {
              const aside = document.querySelector('aside');
              if (!aside) return { phase: '', title: '', body: '' };
              const lines = (aside.innerText || '').trim().split('\n').filter(Boolean);
              return { phase: lines[0] || '', title: lines[2] || '', body: lines[3] || '' };
            }"""
        )

    def focused(self) -> list[str]:
        return self._page.evaluate(
            r"""() => [...document.querySelectorAll('.react-flow__node')]
                 .filter(el => (el.firstElementChild?.style.boxShadow || '').includes('0px 0px 0px 4px'))
                 .map(el => el.getAttribute('data-id'))"""
        )
