from db import get_engine, DBSession, MigrationContext, MonitorrentOperations


upgrades = list()


def add_upgrade(upgrade_func):
    upgrades.append(upgrade_func)


def get_upgrades():
    return upgrades


def core_upgrade(operation_factory):
    with operation_factory() as op:
        if op.has_table('plugin_versions'):
            op.drop_table('plugin_versions')


def upgrade():
    core_upgrade(_operation_factory)
    call_ugprades(upgrades)


def call_ugprades(upgrade_funcs):
    for upgrade_func in upgrade_funcs:
        try:
            upgrade_func(get_engine(), _operation_factory)
        except Exception as e:
            print e


def _operation_factory(session=None):
    if session is None:
        session = DBSession()
    migration_context = MigrationContext.configure(session)
    return MonitorrentOperations(session, migration_context)
