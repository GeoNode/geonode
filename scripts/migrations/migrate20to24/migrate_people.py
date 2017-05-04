#!/usr/bin/python
import utils

src = utils.get_src()
dst = utils.get_dst()
src_cur = src.cursor()
dst_cur = dst.cursor()

select = """select
       auth_user.password,   
       auth_user.last_login, 
       auth_user.is_superuser,
       auth_user.username,   
       auth_user.first_name, 
       auth_user.last_name,  
       auth_user.email auth_user_email,      
       auth_user.is_staff,   
       auth_user.is_active,  
       auth_user.date_joined,
       people_profile.id people_profile_id,          
       people_profile.user_id,     
       people_profile.name,        
       people_profile.organization,
       people_profile.profile,     
       people_profile.position,    
       people_profile.voice,       
       people_profile.fax,         
       people_profile.delivery,    
       people_profile.city,        
       people_profile.area,        
       people_profile.zipcode,     
       people_profile.country,     
       people_profile.email people_profile_email
from   people_profile 
join   auth_user 
on     people_profile.user_id = auth_user.id
order by auth_user.id"""

src_cur.execute(select)

for src_row in src_cur:
    assignments = []
    #id
    #assignments.append(src_row[0])
    #password
    assignments.append(src_row[0])
    #last_login
    assignments.append(src_row[1])
    #is_superuser
    assignments.append(src_row[2])
    #username
    username = src_row[3]
    assignments.append(username)
    #first_name
    assignments.append(src_row[4])
    #last_name
    assignments.append(src_row[5])
    #email
    if src_row[6]:
        email = src_row[6]
    else:
        email = src_row[23]
    if email is None:
        email = 'none@geonode.org'
    assignments.append(email)
    #is_staff
    assignments.append(src_row[7])
    #is_active
    assignments.append(src_row[8])
    #date_joined
    assignments.append(src_row[9])
    #organization
    assignments.append(src_row[13])
    #profile
    assignments.append(src_row[14])
    #position
    assignments.append(src_row[15])
    #voice
    assignments.append(src_row[16])
    #fax
    assignments.append(src_row[17])
    #delivery
    assignments.append(src_row[18])
    #city
    assignments.append(src_row[19])
    #area
    assignments.append(src_row[20])
    #zipcode
    assignments.append(src_row[21])
    #country
    assignments.append(src_row[22])

    try:
        print 'Migrating user %s' % username
        dst_cur.execute("insert into people_profile(password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined, organization, profile, position, voice, fax, delivery, city, area, zipcode, country) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", assignments)
        dst.commit()

    except Exception as error:
        print 
        print type(error)
        print str(error) + select
        print str(src_row)
        dst.rollback()
