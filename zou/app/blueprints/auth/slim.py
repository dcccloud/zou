from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    jwt_required,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
    unset_refresh_cookies,
)
from flask_principal import AnonymousIdentity, Identity, identity_changed
from flask_restful import Resource
from sqlalchemy.exc import OperationalError, TimeoutError

from zou.app import app
from zou.app.blueprints.auth.schemas import LoginSchema
from zou.app.services import auth_service, events_service, persons_service
from zou.app.services.exception import (
    MissingOTPException,
    NoAuthStrategyConfigured,
    TooMuchLoginFailedAttemps,
    UnactiveUserException,
    UserCantConnectDueToNoFallback,
    WrongOTPException,
    WrongPasswordException,
    WrongUserException,
)
from zou.app.stores import auth_tokens_store
from zou.app.utils import permissions, validation
from zou.app.utils.api import configure_api_from_blueprint
from zou.app.utils.flask import is_from_browser


class AuthenticatedResource(Resource):
    @jwt_required()
    def get(self):
        person = persons_service.get_current_user(relations=True)
        organisation = persons_service.get_organisation(
            sensitive=permissions.has_admin_permissions()
        )
        return {
            "authenticated": True,
            "user": person,
            "organisation": organisation,
        }


class LogoutResource(Resource):
    @jwt_required()
    @permissions.require_person
    def get(self):
        try:
            auth_service.logout(get_jwt()["jti"])
            identity_changed.send(
                current_app._get_current_object(), identity=AnonymousIdentity()
            )
        except KeyError:
            return {"Access token not found."}, 500

        logout_data = {"logout": True}
        if is_from_browser(request.user_agent):
            response = jsonify(logout_data)
            unset_jwt_cookies(response)
            return response
        return logout_data


class LoginResource(Resource):
    def post(self):
        body = validation.validate_request_body(LoginSchema)
        email = body.email
        password = body.password

        try:
            user = auth_service.check_auth(
                app,
                email,
                password,
                body.totp,
                body.email_otp,
                None,
                body.recovery_code,
            )

            if auth_service.is_default_password(app, password):
                token = auth_service.generate_reset_token()
                auth_tokens_store.add(
                    "reset-token-%s" % email, token, ttl=3600 * 2
                )
                current_app.logger.info(
                    "User %s must change his password." % email
                )
                return (
                    {
                        "login": False,
                        "default_password": True,
                        "token": token,
                    },
                    400,
                )

            requires_2fa_setup = False
            if app.config["ENFORCE_2FA"]:
                if not auth_service.is_user_exempt_from_2fa(user, app):
                    if not auth_service.person_two_factor_authentication_enabled(
                        user
                    ):
                        requires_2fa_setup = True

            additional_claims = {"identity_type": "person"}
            if requires_2fa_setup:
                additional_claims["requires_2fa_setup"] = True

            access_token = create_access_token(
                identity=user["id"],
                additional_claims=additional_claims,
            )
            refresh_token = create_refresh_token(
                identity=user["id"],
                additional_claims=additional_claims,
            )
            identity_changed.send(
                current_app._get_current_object(),
                identity=Identity(user["id"], "person"),
            )

            ip_address = request.environ.get(
                "HTTP_X_REAL_IP", request.remote_addr
            )
            organisation = persons_service.get_organisation(
                sensitive=user["role"] == "admin"
            )

            response_data = {
                "user": user,
                "organisation": organisation,
                "login": True,
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
            if requires_2fa_setup:
                response_data["two_factor_authentication_required"] = True

            response = jsonify(response_data)
            if is_from_browser(request.user_agent):
                set_access_cookies(response, access_token)
                set_refresh_cookies(response, refresh_token)
                events_service.create_login_log(user["id"], ip_address, "web")
            else:
                events_service.create_login_log(
                    user["id"], ip_address, "script"
                )

            current_app.logger.info(f"User {email} is logged in.")
            return response
        except WrongUserException:
            current_app.logger.info(f"User {email} is not registered.")
            return {"login": False}, 400
        except WrongPasswordException:
            current_app.logger.info(f"User {email} gave a wrong password.")
            return {"login": False}, 400
        except NoAuthStrategyConfigured:
            current_app.logger.info(
                "Authentication strategy is not properly configured."
            )
            return {"login": False}, 409
        except UserCantConnectDueToNoFallback:
            current_app.logger.info(
                f"User {email} can't login due to no fallback from LDAP."
            )
            return {"login": False}, 400
        except TimeoutError:
            current_app.logger.info("Timeout occurs while logging in.")
            return {"login": False}, 400
        except UnactiveUserException:
            current_app.logger.info(f"User {email} is unactive.")
            return (
                {
                    "error": True,
                    "login": False,
                    "message": "User is unactive, he cannot log in.",
                },
                401,
            )
        except TooMuchLoginFailedAttemps:
            current_app.logger.info(
                f"User {email} can't log in due to too much login failed attemps."
            )
            return (
                {
                    "error": True,
                    "login": False,
                    "too_many_failed_login_attemps": True,
                },
                400,
            )
        except MissingOTPException as e:
            current_app.logger.info(
                f"User {email} can't log in due to missing OTP."
            )
            return (
                {
                    "error": True,
                    "login": False,
                    "missing_OTP": True,
                    "preferred_two_factor_authentication": e.preferred_two_factor_authentication,
                    "two_factor_authentication_enabled": e.two_factor_authentication_enabled,
                },
                400,
            )
        except WrongOTPException:
            current_app.logger.info(
                f"User {email} can't log in due to wrong OTP."
            )
            return {"error": True, "login": False, "wrong_OTP": True}, 400
        except OperationalError as exception:
            current_app.logger.error(exception, exc_info=1)
            return (
                {
                    "error": True,
                    "login": False,
                    "message": "Database doesn't seem reachable.",
                },
                500,
            )
        except Exception as exception:
            current_app.logger.error(exception, exc_info=1)
            return {
                "error": True,
                "login": False,
                "message": "A server error occurred. Please contact your administrator.",
            }, 500


class RefreshTokenResource(Resource):
    @jwt_required(refresh=True)
    @permissions.require_person
    def get(self):
        user = persons_service.get_current_user()
        additional_claims = {"identity_type": "person"}

        if app.config["ENFORCE_2FA"]:
            user_unsafe = persons_service.get_current_user(unsafe=True)
            if not auth_service.is_user_exempt_from_2fa(user_unsafe, app):
                if not auth_service.person_two_factor_authentication_enabled(
                    user_unsafe
                ):
                    additional_claims["requires_2fa_setup"] = True

        access_token = create_access_token(
            identity=user["id"],
            additional_claims=additional_claims,
        )
        if is_from_browser(request.user_agent):
            response = jsonify({"refresh": True})
            set_access_cookies(response, access_token)
            unset_refresh_cookies(response)
            return response
        return {"access_token": access_token}


routes = [
    ("/auth/login", LoginResource),
    ("/auth/logout", LogoutResource),
    ("/auth/authenticated", AuthenticatedResource),
    ("/auth/refresh-token", RefreshTokenResource),
]

blueprint = Blueprint("auth", "auth")
api = configure_api_from_blueprint(blueprint, routes)
