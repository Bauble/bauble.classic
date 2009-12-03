#
# all bauble exceptions and errors
#

class BaubleError(Exception):
    def __init__(self, msg=None):
        self.msg = msg
    def __str__(self):
        if self.msg is None:
            return str(type(self).__name__)
        else:
            return '%s: %s' % (type(self).__name__, self.msg)
        return self.msg

class CommitException(Exception):

    def __init__(self, exc, row):
        self.row = row # the model we were trying to commit
        self.exc = exc # the exception thrown while committing

    def __str__(self):
        return str(self.exc)


class DatabaseError(BaubleError):
    pass

class EmptyDatabaseError(DatabaseError):
    pass

class MetaTableError(DatabaseError):
    pass

class TimestampError(DatabaseError):
    pass

class RegistryError(DatabaseError):
    pass

class VersionError(DatabaseError):

    def __init__(self, version):
        super(VersionError, self).__init__()
        self.version = version


class SQLAlchemyVersionError(BaubleError):
    pass

class CheckConditionError(BaubleError):
    pass



def check(condition, msg=None):
    """
    Check that condition is true.  If not then raise
    CheckConditionError(msg)
    """
    if not condition:
        raise CheckConditionError(msg)
