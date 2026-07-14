# Users


## Add a new user

In GeoNode, administrators can manage other users. For example, they can *Add New Users* through the following form.

![add_user_form](img/add_user_form.png)

The form above can be reached from the *Admin Panel* at the following path: *Home > People > Users*. Click on :guilabel:`+  Add user` to open the form page.

![add_user_button](img/add_user_button.png)

It is also available, in the GeoNode UI, the :guilabel:`Add User` link of the *About* menu in the navigation bar.

![add_user_link](img/add_user_link.png)

To perform the user creation fill out the required fields (*username* and *password*) and click on :guilabel:`Save`.
You will be redirected to the *User Details Page* which allows to insert further information about the user.

![user_details_admin_page](img/user_details_admin_page.png)


The user will be visible into the *Users List Page* of the *Admin Panel* and in the *People Page* (see :ref:`user-info`).

![new_user_in_people](img/new_user_in_people.png)


## Activate/Disable a User

When created, new users are *active* by default.
You can check that in the *User Details Page* from the *Admin Panel* (see the picture below).

![new_user_in_people](img/new_user_active.png)

| *Active* users can interact with other users and groups, can manage resources and, more in general, can take actions on the GeoNode platform.
| Untick the *Active* checkbox to disable the user. It will be not considered as user by the GeoNode system.

![new_user_in_people](img/new_user_disabled.png)

## Change a User password

GeoNode administrators can also change/reset the password for those users who forget it.
As shown in the picture below, click on ``this form`` link from the *User Details Page* to access the *Change Password Form*.


![change_user_password_link](img/change_user_password_link.png)


The *Change User Password Form* should looks like the following one.
Insert the new password two times and click on :guilabel:`CHANGE PASSWORD`.

![change_user_password_form](img/change_user_password_form.png)

## Promoting a User to Staff member or superuser


Active users have not access to admin tools.
GeoNode makes available those tools only to *Staff Members* who have the needed permissions.
*Superusers* are staff members with full access to admin tools (all permissions are assigned to them).

Administrators can promote a user to *Staff Member* by ticking the **Staff status** checkbox in the *User Details Page*.
To make some user a *Superuser*, the **Superuser status** checkbox should be ticked. See the picture below.

![staff_and_superuser_permissions](img/staff_and_superuser_permissions.png)
