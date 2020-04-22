import andi

from core_po.objects import is_injectable
from core_po.providers import providers


def build(obj, arguments):
    plan, provider_instances = build_plan(obj, arguments)

    # Build all instances declared as dependencies
    instances = build_instances(plan.dependencies, provider_instances)

    # Fill the obj arguments with the created instances
    kwargs = plan.final_kwargs(instances)
    return obj(**kwargs)


def build_providers(response):
    # FIXME: find out what resources are available
    result = {}
    for cls, provider in providers.items():
        if andi.inspect(provider.__init__):
            result[cls] = provider(response)
        else:
            result[cls] = provider()

    return result


def build_plan(obj, argument):
    """Build a plan for the injection in the obj."""
    provider_instances = build_providers(argument)
    plan = andi.plan(
        obj,
        is_injectable=is_injectable,
        externally_provided=provider_instances.keys()
    )
    return plan, provider_instances


def build_instances(dependencies, providers):
    """Build the instances dict from plan's dependencies."""
    instances = {}
    for cls, kwargs_spec in dependencies:
        if cls in providers:
            # FIXME: handle async providers
            instances[cls] = providers[cls]()
        else:
            # FIXME: understand use case
            instances[cls] = cls(**kwargs_spec.kwargs(instances))

    return instances
