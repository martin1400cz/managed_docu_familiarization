#Subject + message for users - publishing a document
email_subject_accept = "Confirmation of familiarization with the document"
#email_message_for_users = f"Hello,\n\n" \
#                          f"Please confirm that you have read the document.\n\n" \
#                          f"Thank you!"

def email_message_for_users(document_name, link):
    return f"Hello\n" \
    f"Please confirm that you have read the document {document_name}.\n" \
    f"Document link: {link} \n" \
    f"Thank you! ZF team\n"


#Subject + message for users - sending notification from admin/author in document_stats page
email_subject_notification = "Important notice"
#email_message_for_user_notification = "Hello, please confirm that you have read the document."

#Google Drive url prefix
google_drive_prefix = "drive.google.com/file/d/"

#Labels in document_admin_page_form
admin_page_form_document_name = "Document name:"
admin_page_form_document_path = "Document url:"
admin_page_form_document_owner = "Owner"

#Labels in publishing_page_form
publishing_page_form_contact_users="Contact Users"
#Labels in adding_page_form
publishing_page_form_responsible_users="Other responsible persons"
#document_stats_page
user_agreed="Agreed"
user_no_agree_yet="-"

# Groups
all_users_group_name = 'allusers' #All users group name
mdf_admin_group_name = 'MDF_admin' #Group name for mdf admins

# Info text for choosing category in document_author_page
info_text = f"Please select a certain category for the document. <br>" \
            f"- Private documents: Users will not be notified. <br>" \
            f"- Public documents: User will be notified. <br>" \
            f"- Documents for certain groups: User from certain groups will be notified familiarize themselves with the document."

