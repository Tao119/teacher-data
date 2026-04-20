from __future__ import annotations


class TeacherDataError(Exception):
    pass


class TranscriptionError(TeacherDataError):
    pass


class AudioLoadError(TeacherDataError):
    pass


class ConfigError(TeacherDataError):
    pass
