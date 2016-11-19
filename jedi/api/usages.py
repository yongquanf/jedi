from jedi.api import classes
from jedi.parser import tree
from jedi.evaluate import imports
from jedi.evaluate.filters import TreeNameDefinition
from jedi.evaluate.representation import ModuleContext


def usages(evaluator, definition_names, mods):
    """
    :param definitions: list of Name
    """
    def compare_array(definitions):
        """ `definitions` are being compared by module/start_pos, because
        sometimes the id's of the objects change (e.g. executions).
        """
        result = []
        for d in definitions:
            module = d.get_root_context()
            result.append((module, d.start_pos))
        return result

    search_name = list(definition_names)[0].string_name
    compare_definitions = compare_array(definition_names)
    mods = mods | set([d.get_root_context() for d in definition_names])
    definition_names = set(definition_names)
    for m in imports.get_modules_containing_name(evaluator, mods, search_name):
        if isinstance(m, ModuleContext):
            for name_node in m.module_node.used_names.get(search_name, []):
                context = evaluator.create_context(m, name_node)
                result = evaluator.goto(context, name_node)
                if [c for c in compare_array(result) if c in compare_definitions]:
                    name = TreeNameDefinition(context, name_node)
                    definition_names.add(name)
                    # Previous definitions might be imports, so include them
                    # (because goto might return that import name).
                    compare_definitions += compare_array([name])
        else:
            definition_names.add(m.name)

    return [classes.Definition(evaluator, n) for n in definition_names]


def resolve_potential_imports(evaluator, definitions):
    """ Adds the modules of the imports """
    new = set()
    for d in definitions:
        if isinstance(d, TreeNameDefinition):
            imp_or_stmt = d.tree_name.get_definition()
            if isinstance(imp_or_stmt, tree.Import):
                s = imports.ImportWrapper(d.parent_context, d.tree_name)
                new |= resolve_potential_imports(evaluator, set(s.follow(is_goto=True)))
    return set(definitions) | new
