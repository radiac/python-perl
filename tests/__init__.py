# Disable automatic initiation
import builtins


builtins.__dict__["__perl__disable_automatic_import"] = True  # type: ignore
