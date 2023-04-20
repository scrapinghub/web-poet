class FieldMissing(AssertionError):
    pass


class FieldValueIncorrect(AssertionError):
    pass


class FieldsUnexpected(AssertionError):
    pass


class ItemValueIncorrect(AssertionError):
    pass


class ExceptionNotRaised(AssertionError):
    pass


class WrongExceptionRaised(AssertionError):
    pass
