CREATE OR REPLACE FUNCTION geonode_authorize_layer(user_name varchar, type_name varchar) RETURNS varchar AS $$

DECLARE
view_perm integer;
change_perm integer;
roles varchar[] = '{anonymous,NULL}';
ct integer;
user RECORD;
layer RECORD;
customgroup RECORD;
BEGIN

-- get the layer and user, take quick action if we can
SELECT INTO layer "maps_layer"."id", "maps_layer"."owner_id" FROM "maps_layer" WHERE "maps_layer"."typename" = type_name;
if (not FOUND) then
	-- no layer
	return 'nl';
end if;
if (user_name IS NOT NULL) then
	SELECT INTO "user" * FROM "auth_user" WHERE "auth_user"."username" = user_name;
	if (not FOUND) then
		-- no user
		return 'nu';
	end if;
	if ("user".id = layer.owner_id) then
		-- layer owner
		return 'lo-rw';
	end if;
	if ("user".is_superuser) then
		-- super user
		return 'su-rw';
	end if;
	SELECT INTO "customgroup" * FROM "maps_contact" WHERE "maps_contact"."user_id" = "user".id;
	if ("customgroup"."is_org_member") then
	  roles[2] = 'customgroup';
	else
	  roles[2] = 'authenticated';
	end if;
end if;


-- resolve permission and content_type ids
SELECT INTO view_perm "auth_permission"."id"
        FROM "auth_permission" INNER JOIN "django_content_type"
        ON ("auth_permission"."content_type_id" = "django_content_type"."id")
        WHERE ("auth_permission"."codename" = E'view_layer'
        AND "django_content_type"."app_label" = E'maps' );
SELECT INTO change_perm "auth_permission"."id"
	FROM "auth_permission" INNER JOIN "django_content_type"
	ON ("auth_permission"."content_type_id" = "django_content_type"."id")
	WHERE ("auth_permission"."codename" = E'change_layer'
	AND "django_content_type"."app_label" = E'maps' );
SELECT INTO ct "django_content_type"."id"
	FROM "django_content_type"
	WHERE ("django_content_type"."model" = E'layer'
	AND "django_content_type"."app_label" = E'maps' );

-- generic role, read-write
PERFORM "core_genericobjectrolemapping"."object_id"
	FROM "core_genericobjectrolemapping"
	INNER JOIN "core_objectrole"
	ON ("core_genericobjectrolemapping"."role_id" = "core_objectrole"."id")
	INNER JOIN "core_objectrole_permissions"
	ON ("core_objectrole"."id" = "core_objectrole_permissions"."objectrole_id")
	WHERE ("core_genericobjectrolemapping"."subject" = any(roles)
	AND "core_objectrole_permissions"."permission_id" = change_perm
	AND "core_genericobjectrolemapping"."object_ct_id" = ct
	AND "core_genericobjectrolemapping"."object_id" = layer.id
	);
if (FOUND) then return 'gr-rw'; end if;

-- generic role, read-only
PERFORM "core_genericobjectrolemapping"."object_id"
	FROM "core_genericobjectrolemapping"
	INNER JOIN "core_objectrole"
	ON ("core_genericobjectrolemapping"."role_id" = "core_objectrole"."id")
	INNER JOIN "core_objectrole_permissions"
	ON ("core_objectrole"."id" = "core_objectrole_permissions"."objectrole_id")
	WHERE ("core_genericobjectrolemapping"."subject" = any(roles)
	AND "core_objectrole_permissions"."permission_id" = view_perm
	AND "core_genericobjectrolemapping"."object_ct_id" = ct
	AND "core_genericobjectrolemapping"."object_id" = layer.id
	);
if (FOUND) then return 'gr-ro'; end if;

if (user_name IS NOT NULL) then
	-- user role, read-write
	PERFORM "core_userobjectrolemapping"."object_id"
		FROM "core_userobjectrolemapping"
		INNER JOIN "core_objectrole"
		ON ("core_userobjectrolemapping"."role_id" = "core_objectrole"."id")
		INNER JOIN "core_objectrole_permissions"
		ON ("core_objectrole"."id" = "core_objectrole_permissions"."objectrole_id")
		WHERE ("core_objectrole_permissions"."permission_id" = change_perm
		AND "core_userobjectrolemapping"."object_ct_id" = ct
		AND "core_userobjectrolemapping"."user_id" = "user".id
		AND "core_userobjectrolemapping"."object_id" = layer.id
		);
	if (FOUND) then return 'ur-rw'; end if;

	-- user role, read-only
	PERFORM "core_userobjectrolemapping"."object_id"
		FROM "core_userobjectrolemapping"
		INNER JOIN "core_objectrole"
		ON ("core_userobjectrolemapping"."role_id" = "core_objectrole"."id")
		INNER JOIN "core_objectrole_permissions"
		ON ("core_objectrole"."id" = "core_objectrole_permissions"."objectrole_id")
		WHERE ("core_objectrole_permissions"."permission_id" = view_perm
		AND "core_userobjectrolemapping"."object_ct_id" = ct
		AND "core_userobjectrolemapping"."user_id" = "user".id
		AND "core_userobjectrolemapping"."object_id" = layer.id
		);
	if (FOUND) then return 'ur-ro'; end if;
end if;

-- uh oh, nothing found
return 'nf';

END
$$ LANGUAGE plpgsql;
