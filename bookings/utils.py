from bookings.models import Payment

def process_callback(callback_data):
    """Process the callback data from Mpesa"""
    stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
    result_code = stk_callback.get('ResultCode')
    checkout_request_id = stk_callback.get('CheckoutRequestID')
    result_desc = stk_callback.get('ResultDesc', '')

    transaction = Payment.objects.filter(checkout_id=checkout_request_id).first()
    if not transaction:
        return False
    if result_code == 0:
        # Payment successful
        callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
        receipt_number = next((item['Value'] for item in callback_metadata if item['Name'] == 'MpesaReceiptNumber'),
                              None)

        transaction.status = "successful"
        transaction.transaction_id = receipt_number
        transaction.save()

        return True
    elif result_code == 1:
        transaction.status = "failed"
        transaction.description = result_desc or "Payment failed due to an error."
        transaction.save()

        print(f"Transaction failed: {result_desc or 'No description provided.'}")

    elif result_code == 1032:
        transaction.status = "cancelled"
        transaction.description = result_desc or "Transaction was cancelled by the user."
        transaction.save()

        print(f"Transaction cancelled: {result_desc or 'No description provided.'}")
    else:
        transaction.status = "Unknown"
        transaction.description = f"Unhandled result code: {result_code}. {result_desc}"
        transaction.save()

    return False