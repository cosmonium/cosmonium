#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


"""Unit tests for the object-name search controller."""

from direct.task.TaskManagerGlobal import taskMgr

from cosmonium.ui.core.search import NameSearchController


class MockGui:
    def __init__(self, results):
        self.results = results
        self.list_objects_calls = []
        self.get_object_calls = []

    def list_objects(self, prefix):
        self.list_objects_calls.append(prefix)
        return [entry for entry in self.results if entry[0].lower().startswith(prefix.lower())]

    def get_object(self, name):
        self.get_object_calls.append(name)
        for entry in self.results:
            if entry[0] == name:
                return entry[1]
        return None


def make_controller(results, max_results=None):
    gui = MockGui(results)
    updates = []
    controller = NameSearchController(gui, 0.001, lambda: updates.append(True), max_results=max_results)
    return controller, gui, updates


SAMPLE = [('Mars', 'mars-body'), ('Marsden', 'marsden-body'), ('Mercury', 'mercury-body')]


class TestUpdateQuery:
    def test_empty_text_clears_the_list_without_querying_the_gui(self):
        controller, gui, _updates = make_controller(SAMPLE)

        controller.update_query('')

        assert controller.current_list == []
        assert controller.current_selection is None
        assert gui.list_objects_calls == []
        controller.cancel_pending()

    def test_non_empty_text_triggers_the_completion_task(self):
        controller, gui, _updates = make_controller(SAMPLE)
        controller.current_selection = 1

        controller.update_query('mar')

        assert controller.completion_task is not None
        assert controller.completion_task in taskMgr.getAllTasks()
        assert controller.completion_task.delay_time == 0.001
        assert controller.completion_task.getArgs() == ('mar',)

        controller.cancel_pending()

    def test_non_empty_text_queries_the_gui_and_resets_the_selection(self):
        controller, gui, _updates = make_controller(SAMPLE)
        controller.current_selection = 1

        controller._fire_update("mar")
        assert controller.current_list == [('Mars', 'mars-body'), ('Marsden', 'marsden-body')]
        assert controller.current_selection is None
        assert gui.list_objects_calls == ['mar']

    def test_max_results_caps_the_list(self):
        controller, _gui, _updates = make_controller(SAMPLE, max_results=1)

        controller._fire_update("mar")

        assert controller.current_list == [('Mars', 'mars-body')]
        controller.cancel_pending()

    def test_a_new_query_cancels_the_previous_pending_task(self):
        controller, _gui, _updates = make_controller(SAMPLE)

        controller.update_query('m')
        first_task = controller.completion_task
        controller.update_query('ma')

        assert controller.completion_task is not first_task
        assert first_task not in taskMgr.getAllTasks()
        controller.cancel_pending()


class TestMoveSelection:
    def test_move_selection_on_an_empty_list_is_a_no_op(self):
        controller, _gui, updates = make_controller(SAMPLE)

        controller.move_selection(1)

        assert controller.current_selection is None
        assert updates == []

    def test_first_move_selects_the_first_entry_regardless_of_direction(self):
        controller, _gui, updates = make_controller(SAMPLE)
        controller.current_list = SAMPLE

        controller.move_selection(-1)

        assert controller.current_selection == 0
        assert updates == [True]

    def test_move_selection_wraps_around_forward(self):
        controller, _gui, _updates = make_controller(SAMPLE)
        controller.current_list = SAMPLE
        controller.current_selection = len(SAMPLE) - 1

        controller.move_selection(1)

        assert controller.current_selection == 0

    def test_move_selection_wraps_around_backward(self):
        controller, _gui, _updates = make_controller(SAMPLE)
        controller.current_list = SAMPLE
        controller.current_selection = 0

        controller.move_selection(-1)

        assert controller.current_selection == len(SAMPLE) - 1


class TestResolve:
    def test_resolve_returns_the_highlighted_entry_when_one_is_selected(self):
        controller, _gui, _updates = make_controller(SAMPLE)
        controller.current_list = SAMPLE
        controller.current_selection = 1

        assert controller.resolve('irrelevant') == 'marsden-body'

    def test_resolve_falls_back_to_an_exact_gui_lookup_when_nothing_is_selected(self):
        controller, gui, _updates = make_controller(SAMPLE)

        result = controller.resolve('Mercury')

        assert result == 'mercury-body'
        assert gui.get_object_calls == ['Mercury']

    def test_resolve_returns_none_for_an_out_of_range_selection(self):
        controller, _gui, _updates = make_controller(SAMPLE)
        controller.current_list = SAMPLE
        controller.current_selection = 42

        assert controller.resolve('irrelevant') is None


class TestReset:
    def test_reset_clears_state_and_cancels_the_pending_task(self):
        controller, _gui, _updates = make_controller(SAMPLE)
        controller.update_query('mar')

        controller.reset()

        assert controller.current_list == []
        assert controller.current_selection is None
        assert controller.completion_task is None
