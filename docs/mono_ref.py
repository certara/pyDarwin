from docutils import nodes
import docutils.parsers.rst.roles as roles
from sphinx.roles import XRefRole

from docutils.nodes import Element, Node, system_message

from sphinx.environment import BuildEnvironment


class MonoRef(XRefRole):
    def result_nodes(self, document: nodes.document, env: BuildEnvironment, node: Element,
                     is_ref: bool) -> tuple[list[Node], list[system_message]]:
        node['classes'].append('mono')
        return [node], []

    def run(self) -> tuple[list[Node], list[system_message]]:
        self.name = 'std:ref'

        return super().run()


def setup(app):
    roles.register_canonical_role('mono_ref', MonoRef())

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
