# GeoNode Social Accounts

### Introduction

 Through the so-called "social accounts," GeoNode allows authentication through external providers that support the OIDC (OpenID Connect) protocol, such as Google and Microsoft Azure.

 How does it work? Once the authentication provider is configured, GeoNode's sign-on will display a new login button that redirects the user to the external authentication page. After successfully authenticating with the external provider and accepting privacy consents, the browser will redirect the user back to the GeoNode page, prompting them to enter any missing information the first time and automatically authenticating them on subsequent occasions.


### Usage

 Once the provider has been correctly configured (see below), GeoNode will allow the user to login through it.

 The first time you login you will probably need to confirm you `e-mail` and other fields of the `profile`.

!!! note "Important notes"

     If you want a user to be automatically signed as a member of a group, you will need to:

      1. Create the `GroupProfile` in GeoNode
      2. Provide the `groups` or `roles` the user belongs to throguh the `id_token` or `user_info` metadata from the `OIDC` provider itself.

    Notice that, in the case you would like to benefit from this functionality:

      1. Every time the user sing-in again, the groups will be automatically re-assigned by GeoNode, and therefore it won't be possible to assign them manually anymore.
      2. If you need a user to be recognized as a `manager` of the `groups` declared from the provider, you will need to send a claim `is_manager: True` on the user info metadata.

### Quick Configuration


 Currently GeoNode comes with two predefined configurations that you can use to enable either Google or Microsoft Azure.

 **Google**

 1. Add to your `.env` the following settings
        
        SOCIALACCOUNT_OIDC_PROVIDER_ENABLED=True
        SOCIALACCOUNT_PROVIDER=google


 2. Login into GeoNode as an `admin`, go to the `Social Account` settings, create a new `geonode_openid_connect` provider and insert the
        
        Client ID
        Client Secret

 **Microsoft Azure**

 1. Add to your `.env` the following settings
        
        MICROSOFT_TENANT_ID=<the_tenant_id>
        SOCIALACCOUNT_OIDC_PROVIDER_ENABLED=True
        SOCIALACCOUNT_PROVIDER=azure

 2. Login into GeoNode as an `admin`, go to the `Social Account` settings, create a new `geonode_openid_connect` provider and insert the
        
        Client ID
        Client Secret


### Advanced Configuration

 In the case you need to change the default behavior of GeoNode or add a new/custom OIDC provider, you will need to update the `settings` manually as follows.

    SOCIALACCOUNT_PROVIDERS = {
        SOCIALACCOUNT_OIDC_PROVIDER: {
            "NAME": "Your Custom Provider",
            "SCOPE": [
                # Custom scopes comma-separated
            ],
            "AUTH_PARAMS": {
                # Custom AUTH PARAMS
            },
            "COMMON_FIELDS": {"email": "email", "last_name": "family_name", "first_name": "given_name"},  # Custom common fields mappings
            "IS_MANAGER_FIELD": "the_custom_manager_claim",  # This is optional
            "ACCOUNT_CLASS": "the_custom_account_class",
            "ACCESS_TOKEN_URL": "the_custom_token_uri",
            "AUTHORIZE_URL": "the_custom_auth_uri",
            "ID_TOKEN_ISSUER": "the_custom_uri",  # or "PROFILE_URL": "the_custom_user_info_uri"; if you specify the "ID_TOKEN_ISSUER" this will take precedence
            "OAUTH_PKCE_ENABLED": True,
        }
    }


!!! note "Important notes"
    If you specify the "ID_TOKEN_ISSUER" this will take precedence trying to fetch the user info metadata from the `id_token`.

    If the `id_token` won't be available, it will try to fallback to the "PROFILE_URL" uri.

 In the case you will need to customzie how the `Adapter` works and manages the `Groups` registration, you can inject a new class throguh the settings:

    SOCIALACCOUNT_ADAPTER="geonode.people.adapters.GenericOpenIDConnectAdapter"  # This is the default value

#### Social Account Group Synchronization Strategies

GeoNode provides a configurable way to synchronize user group memberships from Social Providers (like Azure or Google) during the login process. This is controlled by the setting `SOCIALACCOUNT_SYNC_USER_GROUPS_ON_LOGIN` which can be defined directly on the settings or in the `ENV` file:

```
SOCIALACCOUNT_SYNC_USER_GROUPS_ON_LOGIN=SAFE_SYNC
```

Three kinds of strategies are supported:

* `FULL_SYNC` (Default): In other words Strict mirroring. On every login, GeoNode wipes all local groups for that user and joins only the groups sent by the provider. This strategy is for environments where the Identity Provider (IdP) is the only source of truth.
* `SAFE_SYNC`: If the provider's response is missing the "groups" or "roles" keys entirely, GeoNode skips the sync to protect existing memberships. If the keys are present (even if empty), a full sync occurs.
* `NO_SYNC`: Total Decoupling. GeoNode ignores group data from the provider. This strategy is for environments where users authenticate via SSO but admins manage permissions manually inside GeoNode.

!!! note Note
    For `FULL_SYNC` and `SAFE_SYNC`, ensure the slug of the GeoNode `GroupProfile` matches the Group ID or role name sent by the provider.