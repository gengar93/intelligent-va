# Address Change for a Split Shipment

## What this illustrates

- Handling an order split across two shipments
- Applying eligibility rules at shipment level
- Collecting missing address information
- Avoiding an all-or-nothing answer when only part of an order can change

## Conversation

**User:** I need to change the address for order ORD-1103.

**Assistant:** **ORD-1103** has two shipments:

- The monitor has already been handed to the courier, so its address can no longer be changed.
- The keyboard is still being prepared, so its address can be changed.

Would you like to update the address for the keyboard?

**User:** Yes, send it to my office.

**Assistant:** I don’t have an office address saved for you. Please provide the street address and postal code.

**User:** 1600 Blake Street, Denver, CO 80202.

**Assistant:** Please confirm this change for the keyboard shipment in **ORD-1103**:

**1600 Blake Street**<br>
**Denver, CO 80202**

The monitor will still go to your original address.

**User:** That’s correct.

**Assistant:** Done. The keyboard will go to your office address. The monitor remains scheduled for delivery to your original address on **August 20**.

**User:** Can you tell the courier to leave the monitor at reception?

**Assistant:** This courier does not accept delivery instructions after dispatch. I can create a support request, or you can use the courier’s tracking page once the package is out for delivery.
