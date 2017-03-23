NEW_REQUEST_EMAIL_TEXT="""
    Hello LiPAD Admins,
    A new {} request has been submitted. You can view the request using the following link:
    {}
    """

NEW_REQUEST_EMAIL_HTML="""
    <p>Hello LiPAD Admins,</p>
    <p>A new {} request has been submitted. You can view the request using the following link:</p>
    <p><a rel="nofollow" target="_blank" href="{}">{}</a></p>
    """

VERIFICATION_EMAIL_TEXT="""
     Dear <strong>{}</strong>,

    Please paste the following URL in your browser to verify your email and complete your Data Request Registration.
    https://{}

    If clicking does not work, try copying and pasting the link to your browser's address bar.
    For inquiries, you can contact us as at {}.

    Regards,
    LiPAD Team
     """
     
VERIFICATION_EMAIL_HTML= """
    <p>Dear <strong>{}</strong>,</p>

   <p>Please click on the following link to verify your email and complete your Data Request Registration.</p>
   <p><a rel="nofollow" target="_blank" href="https://{}">https://{}</a></p>
   <p>If clicking does not work, try copying and pasting the link to your browser's address bar.</p>
   <p>For inquiries, you can contact us as at <a href="mailto:{}" target="_top">{}</a></p>
   </br>
    <p>Regards,</p>
    <p>LiPAD Team</p>
    """

PROFILE_APPROVAL_TEXT= """
    Dear {},
    Your account registration for LiPAD was approved.
    You will now be able to log in using the following log-in credentials:
    username: {}
    
    Before you are able to login to LiPAD, visit first https://ssp.dream.upd.edu.ph/?action=sendtoken and follow the instructions to reset a password for your account.
    You will be able to edit your account details by logging in and going to the following link:
    {}
    
    To download DTMs, DSMs, Classified LAZ and Orthophotos, please proceed to http://lipad.dream.upd.edu.ph/maptiles after logging in.
    To download Flood Hazard Maps, Resource Layers and other datasets, please proceed to http://lipad.dream.upd.edu.ph/layers/.
    If you have any questions, you can contact us as at {}.
    Regards,
    LiPAD Team
     """

PROFILE_APPROVAL_HTML = """
    <p>Dear <strong>{}</strong>,</p>
   <p>Your account registration for LiPAD was approved. You will now be able to log in using the following log-in credentials:</p>
   username: <strong>{}</strong></p>
   <p>Before you are able to login to LiPAD, visit first https://ssp.dream.upd.edu.ph/?action=sendtoken and follow the instructions to reset a password for your account</p></br>
   <p>You will be able to edit your account details by logging in and going to the following link:</p>
   {}
   </br>
   <p>To download DTMs, DSMs, Classified LAZ and Orthophotos, please proceed to <a href="http://lipad.dream.upd.edu.ph/maptiles">Data Tiles Section</a> under Data Store after logging in.</p>
   <p>To download Flood Hazard Maps, Resource Layers and other datasets, please proceed to <a href="http://lipad.dream.upd.edu.ph/layers/">Layers Section</a> under Data Store.</p>
   <p>If you have any questions, you can contact us as at <a href="mailto:{}" target="_top">{}</a></p>
   </br>
    <p>Regards,</p>
    <p>LiPAD Team</p>
    """

PROFILE_REJECTION_TEXT="""
    Dear {},
    Your account registration for LiPAD was not approved.
    Reason: {}
    {}
    If you have further questions, you can contact us as at {}.
    Regards,
    LiPAD Team
     """

PROFILE_REJECTION_HTML="""
    <p>Dear <strong>{}</strong>,</p>
    <p>Your account registration for LiPAD was not approved.</p>
    <p>Reason: {} <br/>
    {}</p>
    <p>If you have further questions, you can contact us as at <a href="mailto:{}" target="_top">{}</a></p>
    </br>
    <p>Regards,</p>
    <p>LiPAD Team</p>
    """

DATA_APPROVAL_TEXT="""
    Dear {},
    Your current data request for LiPAD was approved.
    To download DTMs, DSMs, Classified LAZ and Orthophotos, please proceed to http://lipad.dream.upd.edu.ph/maptiles after logging in.
    To download Flood Hazard Maps, Resource Layers and other datasets, please proceed to http://lipad.dream.upd.edu.ph/layers/.
    To download DTMs, DSMs, Classified LAZ and Orthophotos, please proceed to http://lipad.dream.upd.edu.ph/maptiles after logging in.
    To download Flood Hazard Maps, Resource Layers and other datasets, please proceed to http://lipad.dream.upd.edu.ph/layers/.
    If you have any questions, you can contact us as at {}.
    Regards,
    LiPAD Team
    """

DATA_APPROVAL_HTML= """
    <p>Dear <strong>{}</strong>,</p>
    <p>Your current data request in LiPAD was approved.</p>
    <p>To download DTMs, DSMs, Classified LAZ and Orthophotos, please proceed to <a href="http://lipad.dream.upd.edu.ph/maptiles">Data Tiles Section</a> under Data Store after logging in.</p>
    <p>To download Flood Hazard Maps, Resource Layers and other datasets, please proceed to <a href="http://lipad.dream.upd.edu.ph/layers/">Layers Section</a> under Data Store.</p>
    <p>If you have any questions, you can contact us as at <a href="mailto:{}" target="_top">{}</a></p>
    </br>
    <p>Regards,</p>
    <p>LiPAD Team</p>
    """

DATA_REJECTION_TEXT="""
    Dear {},
    Your data request for LiPAD was not approved.
    Reason: {}
    {}
    If you have further questions, you can contact us as at {}.
    Regards,
    LiPAD Team
    """

DATA_REJECTION_HTML= """
    <p>Dear <strong>{}</strong>,</p>
    <p>Your data request for LiPAD was not approved.</p>
    <p>Reason: {} <br/>
    {}</p>
    <p>If you have further questions, you can contact us as at <a href="mailto:{}" target="_top">{}</a></p>
    </br>
    <p>Regards,</p>
    <p>LiPAD Team</p>
    """

DATA_SUC_FORWARD_NOTIFICATION_TEXT="""
    Greetings, {} {}!
    
    We are informing you that a data requester has requested data which is too big for an FTP transfer to handle.
    We are asking your permission to forward the data to your team and let the requester retrieve the data from you. 
    
    Listed below are the details of the data request:
    Name of Requester: {} {}
    Organization: {}
    Email address: {}
    Project Summary: {}
    Intended Use of Data: {}
    
    We hope to hear your response at the soonest possible time. Thank you!
    
    Regards,
    LiPAD Team
"""

DATA_SUC_FORWARD_NOTIFICATION_HTML="""
    <p>Greetings, {} {}!</p>
    <p>We are informing you that a data requester has requested data which is too big for an FTP transfer to handle.
    We are asking your permission to forward the data to your team and let the requester retrieve the data from you. </p>
    <br/>
    <p>We hope to hear your response at the soonest possible time. Thank you!<p>
    <br />
    <p>Listed below are the details of the data request:<br />
    Name of Requester: {} {}<br />
    Organization: {}<br />
    Email address: {}<br />
    Project Summary: {}<br />
    Intended Use of Data: {}<p>
    <p>Regards,</p>
    <p>LiPAD Team</p>
"""
