Attribute VB_Name = "BuildLinkedSummary"
'======================================================================
' BuildLinkedSummary - refreshes a summary FROM the 12 monthly workbooks.
' Opens each monthly file (read-only), sums the columns, writes totals to a
' "LINKED SUMMARY" sheet in THIS workbook. Re-run any time to refresh
' (after fixing June, run again and the summary updates automatically).
'
' SETUP: save this workbook (as .xlsm) IN THE SAME FOLDER as the 12
'        monthly *_WITH_FORMULAE.xlsx files, then run.
' Columns summed:  GF(188) Gross  GI(191) Other Ded  GJ(192) Total Ded  GK(193) Net
'======================================================================
Option Explicit

Public Sub BuildLinkedSummary()
    Dim folder As String: folder = ThisWorkbook.Path & Application.PathSeparator
    Dim months As Variant, cols As Variant, heads As Variant
    months = Array("April", "May", "June", "July", "August", "September", _
                   "October", "November", "December", "January", "February", "March")
    cols = Array(188, 191, 192, 193)                 ' GF, GI, GJ, GK
    heads = Array("Revised Gross", "Other Deduction", "Total Deduction", "Net Payable")

    Dim sh As Worksheet
    On Error Resume Next
    Set sh = ThisWorkbook.Sheets("LINKED SUMMARY")
    On Error GoTo 0
    If sh Is Nothing Then
        Set sh = ThisWorkbook.Sheets.Add
        sh.Name = "LINKED SUMMARY"
    End If
    sh.Cells.Clear
    sh.Cells(1, 1).Value = "Salary Summary FY25-26 - refreshed from monthly files " & Now
    sh.Cells(3, 1).Value = "Month"
    Dim j As Long
    For j = 0 To UBound(cols): sh.Cells(3, 2 + j).Value = heads(j): Next j

    Application.ScreenUpdating = False
    Application.DisplayAlerts = False

    Dim i As Long, fn As String, wbM As Workbook, wsM As Worksheet, s As Worksheet
    Dim best As Long, rrow As Long, tot As Double
    Dim grand() As Double: ReDim grand(UBound(cols))
    rrow = 4

    For i = 0 To UBound(months)
        fn = Dir(folder & months(i) & "*WITH_FORMULAE.xlsx")
        sh.Cells(rrow, 1).Value = months(i)
        If fn = "" Then
            sh.Cells(rrow, 2).Value = "FILE NOT FOUND"
        Else
            Set wbM = Workbooks.Open(folder & fn, ReadOnly:=True, UpdateLinks:=False)
            best = 0: Set wsM = Nothing
            For Each s In wbM.Worksheets
                If s.UsedRange.Rows.Count > best Then best = s.UsedRange.Rows.Count: Set wsM = s
            Next s
            For j = 0 To UBound(cols)
                tot = Application.WorksheetFunction.Sum(wsM.Columns(CLng(cols(j))))
                sh.Cells(rrow, 2 + j).Value = tot
                sh.Cells(rrow, 2 + j).NumberFormat = "#,##0"
                grand(j) = grand(j) + tot
            Next j
            wbM.Close SaveChanges:=False
        End If
        rrow = rrow + 1
    Next i

    sh.Cells(rrow, 1).Value = "GRAND TOTAL"
    For j = 0 To UBound(cols)
        sh.Cells(rrow, 2 + j).Value = grand(j)
        sh.Cells(rrow, 2 + j).NumberFormat = "#,##0"
    Next j
    sh.Cells(rrow + 1, 1).Value = "In Rs crore"
    For j = 0 To UBound(cols)
        sh.Cells(rrow + 1, 2 + j).Value = grand(j) / 10000000
        sh.Cells(rrow + 1, 2 + j).NumberFormat = "#,##0.00"
    Next j
    sh.Columns.AutoFit

    Application.DisplayAlerts = True
    Application.ScreenUpdating = True
    MsgBox "Summary refreshed." & vbCrLf & _
           "Gross total = " & Format(grand(0), "#,##0") & _
           "  (Rs " & Format(grand(0) / 10000000, "#,##0.00") & " cr)", vbInformation
End Sub
