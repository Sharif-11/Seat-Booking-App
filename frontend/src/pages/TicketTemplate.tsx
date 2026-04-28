const TicketTemplate = ({ bookingData }: { bookingData: any }) => {
  const departureDate = new Date(bookingData.show.departure_time)

  const date = departureDate.toLocaleDateString('en-BD', {
    day: '2-digit',
    month: 'short',
  })

  const time = departureDate.toLocaleTimeString('en-BD', {
    hour: '2-digit',
    minute: '2-digit',
  })

  const seats = bookingData.seats.map((s: any) => s.seat_label || s.seat_id).join(',')

  return (
    <div
      style={{
        width: '320px',
        margin: '20px auto',
        fontFamily: 'Inter, sans-serif',
      }}
    >
      <div
        style={{
          borderRadius: '12px',
          background: '#fff',
          boxShadow: '0 6px 16px rgba(0,0,0,0.12)',
          overflow: 'hidden',
        }}
      >
        {/* Top strip */}
        <div
          style={{
            background: '#1a73e8',
            color: '#fff',
            padding: '8px 10px',
            fontSize: '11px',
            display: 'flex',
            justifyContent: 'space-between',
          }}
        >
          <span style={{ fontWeight: 600 }}>{bookingData.show.title || 'Bus'}</span>
          <span>#{bookingData.booking_id}</span>
        </div>

        {/* Route */}
        <div
          style={{
            padding: '8px 10px',
            fontSize: '13px',
            fontWeight: 700,
            textAlign: 'center',
            borderBottom: '1px dashed #ddd',
          }}
        >
          {bookingData.show.from_location} → {bookingData.show.to_location}
        </div>

        {/* Main Info Row */}
        <div
          style={{
            display: 'flex',
            padding: '8px 10px',
            fontSize: '11px',
            alignItems: 'center',
          }}
        >
          {/* Left info */}
          <div style={{ flex: 1, lineHeight: 1.5 }}>
            <div>
              <b>{date}</b> • {time}
            </div>
            <div>
              Seat: <b>{seats}</b>
            </div>
            <div>Pax: {bookingData.seats.length}</div>
            <div>৳{bookingData.total_amount}</div>
          </div>

          {/* QR */}
          <div
            style={{
              width: '55px',
              height: '55px',
              background: '#f1f5f9',
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '9px',
            }}
          >
            QR
          </div>
        </div>

        {/* Footer tiny */}
        <div
          style={{
            fontSize: '9px',
            padding: '6px 10px',
            color: '#777',
            borderTop: '1px solid #eee',
            textAlign: 'center',
          }}
        >
          Show at boarding
        </div>
      </div>
    </div>
  )
}
export const generateTicketPDF = async (bookingData: any) => {
  try {
    // Dynamically import required libraries
    const html2canvas = (await import('html2canvas')).default
    const { jsPDF } = await import('jspdf')

    // Create a temporary div to render the ticket
    const tempDiv = document.createElement('div')
    tempDiv.style.position = 'absolute'
    tempDiv.style.left = '-9999px'
    tempDiv.style.top = '0'
    tempDiv.style.background = '#f5f7fa'
    tempDiv.style.padding = '20px'
    document.body.appendChild(tempDiv)

    // Render React component to HTML
    const { createRoot } = await import('react-dom/client')
    const root = createRoot(tempDiv)
    root.render(<TicketTemplate bookingData={bookingData} />)

    // Wait for rendering and fonts to load
    await new Promise(resolve => setTimeout(resolve, 300))

    // Capture the ticket as canvas
    const ticketElement = tempDiv.firstChild as HTMLElement
    const canvas = await html2canvas(ticketElement, {
      scale: 2.5,
      backgroundColor: '#f5f7fa',
      logging: false,
      useCORS: true,
      windowWidth: ticketElement.scrollWidth,
      windowHeight: ticketElement.scrollHeight,
      onclone: (clonedDoc, element) => {
        // Ensure any dynamic styles are applied
        if (element) {
          element.style.background = '#f5f7fa'
        }
      },
    })

    // Clean up
    root.unmount()
    document.body.removeChild(tempDiv)

    // Create PDF with optimized dimensions
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
      compress: true,
    })

    const pdfWidth = pdf.internal.pageSize.getWidth()
    const pdfHeight = pdf.internal.pageSize.getHeight()

    // Calculate image dimensions to fit nicely on A4
    const margin = 10
    const imgWidth = pdfWidth - margin * 2
    const imgHeight = (canvas.height * imgWidth) / canvas.width

    let position = margin

    // Add image to PDF with high quality
    pdf.addImage(imgData, 'PNG', margin, position, imgWidth, imgHeight, undefined, 'FAST')

    // Add a second page if content overflows (unlikely with our design)
    if (position + imgHeight > pdfHeight - margin) {
      pdf.addPage()
      const remainingHeight = position + imgHeight - (pdfHeight - margin)
      const remainingY = margin - remainingHeight
      pdf.addImage(imgData, 'PNG', margin, remainingY, imgWidth, imgHeight, undefined, 'FAST')
    }

    // Save PDF with clean filename
    const filename = `BusTicket_${bookingData.booking_id}_${bookingData.show.from_location}_to_${bookingData.show.to_location}.pdf`
    pdf.save(filename)

    return { success: true, filename }
  } catch (error) {
    console.error('PDF generation error:', error)
    throw new Error('Failed to generate PDF. Please ensure all required libraries are installed.')
  }
}

// Updated handler function for React component

// Example usage in a React component:
// <button
//   onClick={handleDownloadTicket}
//   disabled={isDownloading}
//   style={{
//     background: '#1a73e8',
//     color: 'white',
//     border: 'none',
//     borderRadius: '40px',
//     padding: '12px 28px',
//     fontWeight: '600',
//     cursor: 'pointer',
//     boxShadow: '0 2px 6px rgba(0,0,0,0.1)'
//   }}
// >
//   {isDownloading ? 'Generating PDF...' : '📄 Download Ticket PDF'}
// </button>
