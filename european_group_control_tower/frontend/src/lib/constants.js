export const APP_NAME = 'EUROPEAN GROUP | CONTROL TOWER';

export const STAGES = ['PO Issued', 'Booked', 'At Sea', 'Arrived Port', 'Customs Cleared', 'In Inventory'];
export const CUSTOMS_STATUSES = ['Not Started', 'In Progress', 'Held', 'Cleared'];
export const PAYMENT_STATUSES = ['Unpaid', 'Partial', 'Paid'];
export const PAYMENT_METHODS = ['', 'Bank Transfer (T/T)', 'Letter of Credit', 'Cash Against Documents', 'Cheque', 'Cash', 'Other'];
export const CURRENCIES = ['USD', 'EUR', 'EGP', 'CNY', 'GBP'];

export const DOC_TYPES = [
  'Proforma Invoice', 'Commercial Invoice', 'Packing List', 'Bill of Lading', 'Certificate of Origin',
  'Certificate of Analysis', 'Insurance', 'ACID', 'Customs', 'Other',
];
export const DOC_STATUSES = ['Missing', 'Pending', 'Received', 'Expired'];
// Documents that must exist once a shipment has sailed (ACID is checked for every open PO).
export const REQUIRED_DOCS = ['Commercial Invoice', 'Packing List', 'Bill of Lading', 'Certificate of Origin', 'ACID'];

export const ARRIVING_SOON_DAYS = 7;
export const PAYMENT_SOON_DAYS = 7;

// Import field catalogue: key, label and header synonyms (matched after lower-casing and stripping punctuation).
export const IMPORT_FIELDS = [
  { key: 'poNumber', label: 'PO Number', required: true, syn: ['po', 'ponumber', 'pono', 'ponum', 'purchaseorder', 'orderreference', 'orderref', 'order', 'orderno'] },
  { key: 'poDate', label: 'PO Date', syn: ['podate', 'orderdate', 'date'] },
  { key: 'supplier', label: 'Supplier', syn: ['supplier', 'vendor', 'suppliername', 'company', 'manufacturer'] },
  { key: 'product', label: 'Product', syn: ['product', 'item', 'description', 'productname', 'goods'] },
  { key: 'category', label: 'Category', syn: ['category', 'productcategory', 'group'] },
  { key: 'rep', label: 'Purchase Rep.', syn: ['purchaserep', 'rep', 'buyer', 'purchaser', 'owner', 'responsible'] },
  { key: 'quantity', label: 'Quantity', syn: ['quantity', 'qty'] },
  { key: 'unit', label: 'Unit', syn: ['unit', 'uom'] },
  { key: 'unitPrice', label: 'Unit Price', syn: ['unitprice', 'price', 'rate'] },
  { key: 'invoice', label: 'Invoice', syn: ['invoice', 'invoiceno', 'invoicenumber', 'inv'] },
  { key: 'bl', label: 'BL Number', syn: ['blnumber', 'bl', 'blno', 'billoflading', 'bol'] },
  { key: 'booking', label: 'Booking', syn: ['booking', 'bookingno', 'bookingnumber'] },
  { key: 'acid', label: 'ACID', syn: ['acid', 'acidnumber', 'acidno'] },
  { key: 'container', label: 'Container', syn: ['container', 'containerno', 'containernumber'] },
  { key: 'tracking', label: 'Tracking Number', syn: ['tracking', 'trackingnumber', 'trackingno', 'trackno'] },
  { key: 'trackingUrl', label: 'Tracking URL', syn: ['trackingurl', 'trackinglink', 'url', 'link'] },
  { key: 'carrier', label: 'Carrier', syn: ['shippingline', 'carrier', 'line', 'shippingcompany'] },
  { key: 'vessel', label: 'Vessel', syn: ['vessel', 'vesselname', 'ship'] },
  { key: 'voyage', label: 'Voyage', syn: ['voyage', 'voyageno', 'voy'] },
  { key: 'etd', label: 'ETD', syn: ['etd', 'departure', 'departuredate'] },
  { key: 'eta', label: 'ETA', syn: ['eta', 'arrival', 'expectedarrival'] },
  { key: 'actualArrival', label: 'Actual Arrival', syn: ['actualarrival', 'ata', 'arrivaldate', 'arrivedon'] },
  { key: 'location', label: 'Current Location', syn: ['currentlocation', 'location', 'position'] },
  { key: 'destination', label: 'Destination Port', syn: ['destination', 'destinationport', 'pod', 'portofdischarge'] },
  { key: 'registration', label: 'Registration', syn: ['registration', 'registered'] },
  { key: 'customs', label: 'Customs', syn: ['customs', 'customsstatus', 'clearance'] },
  { key: 'status', label: 'Status', syn: ['status', 'stage', 'shipmentstatus'] },
  { key: 'paymentStatus', label: 'Payment Status', syn: ['paymentstatus', 'payment'] },
  { key: 'paymentDue', label: 'Payment Due', syn: ['paymentdue', 'duedate', 'due'] },
  { key: 'total', label: 'Total', syn: ['total', 'totalamount', 'value', 'ordervalue', 'amountdue'] },
  { key: 'paid', label: 'Paid', syn: ['paid', 'amountpaid', 'paidamount'] },
  { key: 'remaining', label: 'Remaining', syn: ['remaining', 'balance', 'outstanding'] },
  { key: 'currency', label: 'Currency', syn: ['currency', 'ccy'] },
  { key: 'notes', label: 'Notes', syn: ['notes', 'note', 'remarks', 'comment', 'comments'] },
  { key: 'country', label: 'Supplier Country', syn: ['country', 'suppliercountry', 'origin'] },
];
