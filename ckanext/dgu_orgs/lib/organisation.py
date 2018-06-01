from ckan import model
import logging

log = logging.getLogger(__name__)

def go_up_tree(organisation):
    '''Provided with a organisation object, it walks up the hierarchy and yields
    each organisation, including the one you supply.

    Essentially this is a slower version of Group.get_parent_group_hierarchy
    because it returns Group objects, rather than dicts. And it includes the
    organisation you supply.
    '''
    yield organisation
    for parent in organisation.get_parent_groups(type='organization'):
        for grandparent in go_up_tree(parent):
            yield grandparent

def go_down_tree(organisation):
    '''Provided with a organisation object, it walks down the hierarchy and yields
    each organisation, including the one you supply.

    Essentially this is a slower version of Group.get_children_group_hierarchy
    because it returns Group objects, rather than dicts.
    '''
    yield organisation
    for child in organisation.get_children_groups(type='organization'):
        for grandchild in go_down_tree(child):
            yield grandchild

def find_group_admins(group):
    '''Look for organisation admins up the tree'''
    recipients = []
    recipient_org = None
    for organisation in go_up_tree(group):
        admins = organisation.members_of_type(model.User, 'admin').all()
        if admins:
            recipients = [(u.fullname,u.email) for u in admins]
            recipient_org = organisation.title
            break

    return recipients, recipient_org

def cached_openness_scores(reports_to_run=None):
    """
    This function is called by the ICachedReport plugin which will
    iterate over all of the organisations and generate an openness score
    for them on a regular basis
    """
    import json
    from ckan.lib.json import DateTimeJsonEncoder

    local_reports = set(['openness-scores', 'openness-scores-withsub'])
    if reports_to_run:
      local_reports = set(reports_to_run) & local_reports

    if not local_reports:
      return

    # TODO ASH HERE
    organisations = model.Session.query(model.Group).\
        filter(model.Group.type=='organisation').\
        filter(model.Group.state=='active')

    log.info("Generating openness-scores report")
    log.info("Fetching %d organisations" % organisations.count())

    for organisation in organisations.all():
        # Run the openness report with and without include_sub_orgs set
        if 'openness-scores' in local_reports:
          log.info("Generating openness scores for %s" % organisation.name)
          val = openness_scores(organisation, use_cache=False)
          model.DataCache.set(organisation.name, "openness-scores",
                              json.dumps(val,cls=DateTimeJsonEncoder))

        if 'openness-scores-withsub' in local_reports:
          val = openness_scores(organisation, include_sub_orgs=True,
                                use_cache=False)
          model.DataCache.set(organisation.name, "openness-scores-withsub",
                              json.dumps(val,cls=DateTimeJsonEncoder))

    model.Session.commit()

def openness_scores(organisation, include_sub_orgs=False, use_cache=True):
    """
        For the provided organisation, this grabs the resource ids
        and finds the matching openness scores in the task_status
        table to return a total number of entries (which should be
        the same as the resource count) and dictionary containing
        a count for each score such as {0:3, 1:0, 2:1 ...}
    """
    from collections import defaultdict

    if use_cache:
        key = 'openness-scores'
        if include_sub_orgs:
            key = "".join([key, '-withsub'])
        cache = model.DataCache.get_fresh(organisation.name, key)
        if cache:
            log.info("Found openness score in cache: %s" % cache)
            return cache


    q = """SELECT TS.value::INT from task_status  as TS
           WHERE TS.task_type='qa' AND
                 TS.entity_type ='resource' AND
                 TS.key = 'openness_score' AND
                 TS.entity_id in (
                   SELECT R.id from resource  as R
                   INNER JOIN resource_group as RG ON RG.id = R.resource_group_id
                   INNER JOIN package as P ON P.id = RG.package_id
                   WHERE P.state = 'active' AND R.state='active' AND
                         P.id in (SELECT table_id FROM member
                                  WHERE group_id in ({org_id})
                                  AND table_name='package' AND state='active')
                                 );"""

    d = defaultdict(int)

    if include_sub_orgs:
        orgids = ["'%s'" % o.id for o in go_down_tree(organisation)]
    else:
        orgids = ["'%s'" % organisation.id]

    for m in model.Session.execute(q.format(org_id=','.join(orgids))):
        d[str(m[0])] += 1
    total = sum(d.values())

    return total, d


def resource_count(organisation, include_sub_organisations=False):
    """
        Counts the number of active resources within active datasets and
        returns the scalar.
    """
    q = """SELECT count(R.id) from resource  as R
           INNER JOIN resource_group as RG ON RG.id = R.resource_group_id
           INNER JOIN package as P ON P.id = RG.package_id
           WHERE P.state = 'active' AND R.state='active' AND
                 P.id in (SELECT table_id FROM member
                          WHERE group_id IN ({org_id})
                          AND table_name='package' AND state='active');"""

    if include_sub_organisations:
        orgids = ["'%s'" % o.id for o in go_down_tree(organisation)]
    else:
        orgids = ["'%s'" % organisation.id]

    return model.Session.scalar(q.format(org_id=','.join(orgids)))

