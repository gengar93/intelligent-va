# Address Change for a Split Shipment

## What this illustrates

- Handling an order split across two shipments
- Applying eligibility rules at shipment level
- Collecting missing address information
- Avoiding an all-or-nothing answer when only part of an order can change

## Conversation

**User:** I need to change the address for order ORD-1103.

**Assistant:** **ORD-1103** has two shipments:

- The desk lamp has already been handed to the courier, so its address can no longer be changed.
- The notebook set is still being prepared, so its address can be changed.

Would you like to update the address for the notebook set?

**User:** Yes, send it to my office.

**Assistant:** I don’t have an office address saved for you. Please provide the street address and postal code.

**User:** 14 Park View Road, Indiranagar, Bengaluru 560038.

**Assistant:** Please confirm this change for the notebook shipment in **ORD-1103**:

**14 Park View Road**  
**Indiranagar, Bengaluru 560038**

The desk lamp will still go to your original address.

**User:** That’s correct.

**Assistant:** Done. The notebook shipment will go to your office address. The desk lamp remains scheduled for delivery to your original address on **10 August**.

**User:** Can you tell the courier to leave the lamp with security?

**Assistant:** This courier does not accept delivery instructions after dispatch. I can create a support request, or you can use the courier’s tracking page once the package is out for delivery.

