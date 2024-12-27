#Subject + message for users - publishing a document
email_subject_accept = "Confirmation of familiarization with the document"
#email_message_for_users = f"Hello,\n\n" \
#                          f"Please confirm that you have read the document.\n\n" \
#                          f"Thank you!"

def email_message_for_users(link):
    return f"Hello,\n\n" \
    f"Please confirm that you have read the document.\n" \
    f"Document link: {link} \n" \
    f"Thank you!"


#Subject + message for users - sending notification from admin/author in document_stats page
email_subject_notification = "Important notice"
#email_message_for_user_notification = "Hello, please confirm that you have read the document."
#Labels in admin_file_search_page_form
admin_page_form_document_name = "Document name:"
admin_page_form_document_path = "Document url:"
admin_page_form_document_owner = "Owner"
#Labels in publishing_page_form
publishing_page_form_contact_users="Selected Users"
#document_stats_page
user_agreed="Agreed"
user_no_agree_yet="-"

