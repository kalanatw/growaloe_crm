import React from 'react';
import { NewCreateInvoicePage } from '../pages/NewCreateInvoicePage';

export const InvoiceCreateRedirect: React.FC = () => {
  // Since the route is now owner-only, we can directly show NewCreateInvoicePage
  return <NewCreateInvoicePage />;
};
