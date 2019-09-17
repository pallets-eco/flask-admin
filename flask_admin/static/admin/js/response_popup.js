let initData = JSON.parse(document.getElementById('flask-admin-popup-response').dataset.popupResponse);
window.opener.dismissAddRelatedObjectPopup(window, initData.value, initData.obj_name);
