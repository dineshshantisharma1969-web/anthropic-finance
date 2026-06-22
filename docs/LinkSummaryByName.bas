Attribute VB_Name = "LinkSummaryByName"
'======================================================================
' LinkSummaryByName - fills the "Monthly Summary" sheet from the 12 monthly
' *_WITH_FORMULAE.xlsx files, matching each field BY HEADER NAME (so it works
' even though column positions differ month to month). Keeps summary small.
'
' SETUP: save a COPY of the summary workbook as .xlsm IN THE SAME FOLDER as the
'        12 monthly files, then run this. Re-run any time to refresh.
'
' Summary rows: April=5 ... March=16.  Formula cols (Z, AB, AD) are not touched.
'======================================================================
Option Explicit

Public Sub LinkSummaryByName()
    Const SUMSHEET As String = "Monthly Summary"
    Dim months As Variant
    months = Array("April", "May", "June", "July", "August", "September", _
                   "October", "November", "December", "January", "February", "March")
    ' summaryCol | monthly header name (normalized: UPPER, no spaces/_/./()/-)
    Dim map As Variant
    map = Array("3|REVISEDGROSSNEWFINAL", "4|REVISEDPF", "5|ESIC1", "6|PT1", "7|LWF1", _
        "8|TDS1", "9|EMPLOYEEWELFAREFUND1", "10|ADVANCE1", "11|UNIFORM1", "12|OTHERDEDUCTION1", _
        "13|FOODDEDUCTION1", "14|FOODDEDUCTIONS1", "15|MOBILEDEDUCTION1", "16|PROFESSIONALFEES1", _
        "17|INSURANCEDEDUCTION1", "18|INSURANCE1", "19|FINE1", "20|ACCOMODATION1", "21|FLEXIDED1", _
        "22|CONVEYANCEALLDED1", "23|LAUNDRYCHARGES1", "24|MEALDEDUCTION1", "25|REFYNEADVANCE1", _
        "27|OTHERDEDUCTION", "29|REVISEDNETPAYABLE")

    Dim sumSh As Worksheet: Set sumSh = ThisWorkbook.Sheets(SUMSHEET)
    Dim folder As String: folder = ThisWorkbook.Path & Application.PathSeparator

    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    Dim report As String

    Dim i As Long, rowS As Long, fn As String, wb As Workbook, ws As Worksheet, s As Worksheet, best As Long
    For i = 0 To UBound(months)
        rowS = 5 + i
        fn = Dir(folder & months(i) & "*WITH_FORMULAE.xlsx")
        If fn = "" Then
            report = report & months(i) & ": FILE NOT FOUND" & vbCrLf
            GoTo NextMonth
        End If

        Set wb = Workbooks.Open(folder & fn, ReadOnly:=True, UpdateLinks:=False)
        best = 0: Set ws = Nothing
        For Each s In wb.Worksheets
            If s.UsedRange.Rows.Count > best Then best = s.UsedRange.Rows.Count: Set ws = s
        Next s

        ' find header row (search for the gross-new header in first 15 rows)
        Dim hr As Long, c As Long, t As String, maxC As Long
        maxC = ws.UsedRange.Column + ws.UsedRange.Columns.Count - 1
        hr = 0
        Dim rscan As Long
        For rscan = 1 To 15
            For c = 1 To maxC
                If NormU(ws.Cells(rscan, c).Value) = "REVISEDGROSSNEWFINAL" Then hr = rscan: Exit For
            Next c
            If hr > 0 Then Exit For
        Next rscan
        If hr = 0 Then hr = 1

        ' build header-name -> column dictionary (first occurrence wins)
        Dim dict As Object: Set dict = CreateObject("Scripting.Dictionary")
        For c = 1 To maxC
            t = NormU(ws.Cells(hr, c).Value)
            If Len(t) > 0 Then If Not dict.Exists(t) Then dict.Add t, c
        Next c

        ' last data row from the gross-new column
        Dim gcol As Long, lastR As Long
        gcol = 0: If dict.Exists("REVISEDGROSSNEWFINAL") Then gcol = dict("REVISEDGROSSNEWFINAL")
        If gcol = 0 Then
            report = report & months(i) & ": REVISED_GROSS_NEW not found - skipped" & vbCrLf
            wb.Close SaveChanges:=False
            GoTo NextMonth
        End If
        lastR = ws.Cells(ws.Rows.Count, gcol).End(xlUp).Row

        ' employee rows = count of EMPCODE
        If dict.Exists("EMPCODE") Then
            sumSh.Cells(rowS, 2).Value = Application.WorksheetFunction.CountA( _
                ws.Range(ws.Cells(hr + 1, dict("EMPCODE")), ws.Cells(lastR, dict("EMPCODE"))))
        End If

        ' map each field by name
        Dim p As Variant, parts() As String, scol As Long, nm As String, miss As String
        For Each p In map
            parts = Split(CStr(p), "|")
            scol = CLng(parts(0)): nm = parts(1)
            If dict.Exists(nm) Then
                sumSh.Cells(rowS, scol).Value = Application.WorksheetFunction.Sum( _
                    ws.Range(ws.Cells(hr + 1, dict(nm)), ws.Cells(lastR, dict(nm))))
                sumSh.Cells(rowS, scol).NumberFormat = "#,##0"
            Else
                miss = miss & nm & " "
            End If
        Next p
        If Len(miss) > 0 Then report = report & months(i) & ": missing -> " & miss & vbCrLf

        wb.Close SaveChanges:=False
NextMonth:
    Next i

    Application.DisplayAlerts = True
    Application.ScreenUpdating = True

    If Len(report) = 0 Then report = "All 12 months linked successfully."
    MsgBox "Summary refreshed by header name." & vbCrLf & vbCrLf & report, vbInformation
End Sub

Private Function NormU(v As Variant) As String
    Dim s As String: s = UCase(CStr(v))
    Dim ch As Variant
    For Each ch In Array(" ", "_", ".", "(", ")", "-", "/", vbLf, vbCr)
        s = Replace(s, CStr(ch), "")
    Next ch
    NormU = s
End Function
