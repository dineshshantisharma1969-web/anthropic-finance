Attribute VB_Name = "LinkSummaryTraceable"
'======================================================================
' LinkSummaryTraceable - writes LIVE, CLICKABLE formulas into the
' "Monthly Summary" sheet so every figure traces to the monthly file.
'
'  * Deductions + Net  -> =SUM('[<month file>]<sheet>'!<col>)   (column found
'                         BY NAME each month; VERIFIED to equal your current
'                         figure before it links, else left alone + reported).
'  * Gross (C) & Other-Ded-Residual (AA) -> =SUM(monthly col) - reduction
'                         (keeps your 380cr value, shows source minus the cut).
'
' SETUP: save a COPY of the summary as .xlsm IN THE SAME FOLDER as the 12
'        monthly *_WITH_FORMULAE.xlsx files, then run. If Excel asks to
'        "Update Links" when reopening, click Update / Enable Content.
'======================================================================
Option Explicit

Public Sub LinkSummaryTraceable()
    Const SUMSHEET As String = "Monthly Summary"
    Dim months As Variant
    months = Array("April", "May", "June", "July", "August", "September", _
                   "October", "November", "December", "January", "February", "March")
    ' summaryCol | monthly header (normalized) | mode  (A=adjusted, L=link+verify)
    Dim map As Variant
    map = Array("3|REVISEDGROSS|A", "4|REVISEDPF|L", "5|ESIC1|L", "6|PT1|L", "7|LWF1|L", _
        "8|TDS1|L", "9|EMPLOYEEWELFAREFUND1|L", "10|ADVANCE1|L", "11|UNIFORM1|L", "12|OTHERDEDUCTION1|L", _
        "13|FOODDEDUCTION1|L", "14|FOODDEDUCTIONS1|L", "15|MOBILEDEDUCTION1|L", "16|PROFESSIONALFEES1|L", _
        "17|INSURANCEDEDUCTION1|L", "18|INSURANCE1|L", "19|FINE1|L", "20|ACCOMODATION1|L", "21|FLEXIDED1|L", _
        "22|CONVEYANCEALLDED1|L", "23|LAUNDRYCHARGES1|L", "24|MEALDEDUCTION1|L", "25|REFYNEADVANCE1|L", _
        "27|OTHERDEDUCTION|A", "29|REVISEDNETPAYABLE|L")

    Dim sumSh As Worksheet: Set sumSh = ThisWorkbook.Sheets(SUMSHEET)
    Dim folder As String: folder = ThisWorkbook.Path & Application.PathSeparator
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    Dim report As String

    Dim i As Long, rowS As Long, fn As String, wb As Workbook, ws As Worksheet, s As Worksheet, best As Long
    For i = 0 To UBound(months)
        rowS = 5 + i
        fn = Dir(folder & months(i) & "*WITH_FORMULAE.xlsx")
        If fn = "" Then report = report & months(i) & ": FILE NOT FOUND" & vbCrLf: GoTo NextMonth

        Set wb = Workbooks.Open(folder & fn, ReadOnly:=True, UpdateLinks:=False)
        best = 0: Set ws = Nothing
        For Each s In wb.Worksheets
            If s.UsedRange.Rows.Count > best Then best = s.UsedRange.Rows.Count: Set ws = s
        Next s

        Dim hr As Long, c As Long, maxC As Long, rscan As Long
        maxC = ws.UsedRange.Column + ws.UsedRange.Columns.Count - 1
        hr = 0
        For rscan = 1 To 15
            For c = 1 To maxC
                If NormU(ws.Cells(rscan, c).Value) = "REVISEDGROSS" Then hr = rscan: Exit For
            Next c
            If hr > 0 Then Exit For
        Next rscan
        If hr = 0 Then hr = 1

        Dim dict As Object: Set dict = CreateObject("Scripting.Dictionary")
        Dim t As String
        For c = 1 To maxC
            t = NormU(ws.Cells(hr, c).Value)
            If Len(t) > 0 Then If Not dict.Exists(t) Then dict.Add t, c
        Next c

        Dim gcol As Long, lastR As Long
        gcol = 0: If dict.Exists("REVISEDGROSS") Then gcol = dict("REVISEDGROSS")
        If gcol = 0 Then report = report & months(i) & ": REVISED_GROSS not found - skipped" & vbCrLf: wb.Close False: GoTo NextMonth
        lastR = ws.Cells(ws.Rows.Count, gcol).End(xlUp).Row

        Dim shName As String: shName = ws.Name
        Dim base As String: base = "'" & folder & "[" & fn & "]" & shName & "'!"

        Dim p As Variant, parts() As String, scol As Long, nm As String, mode As String
        Dim mc As Long, L As String, msum As Double, cur As Double, adj As Double, miss As String, mism As String
        For Each p In map
            parts = Split(CStr(p), "|")
            scol = CLng(parts(0)): nm = parts(1): mode = parts(2)
            If Not dict.Exists(nm) Then miss = miss & nm & " ": GoTo NextField
            mc = dict(nm): L = ColLetter(mc)
            msum = Application.WorksheetFunction.Sum(ws.Range(ws.Cells(hr + 1, mc), ws.Cells(lastR, mc)))
            cur = ValD(sumSh.Cells(rowS, scol).Value)
            Dim rngRef As String
            rngRef = "SUM(" & base & "$" & L & "$" & (hr + 1) & ":$" & L & "$" & lastR & ")"
            If mode = "A" Then
                adj = msum - cur                         ' = the documented reduction
                sumSh.Cells(rowS, scol).Formula = "=" & rngRef & "-" & Format(adj, "0")
            Else
                If Abs(msum - cur) <= 2 Then
                    sumSh.Cells(rowS, scol).Formula = "=" & rngRef
                Else
                    mism = mism & nm & "(file " & Format(msum, "#,##0") & " vs sheet " & Format(cur, "#,##0") & ") "
                End If
            End If
            sumSh.Cells(rowS, scol).NumberFormat = "#,##0"
NextField:
        Next p
        If Len(miss) > 0 Then report = report & months(i) & ": NOT FOUND -> " & miss & vbCrLf
        If Len(mism) > 0 Then report = report & months(i) & ": VALUE MISMATCH (left as-is) -> " & mism & vbCrLf

        wb.Close SaveChanges:=False
NextMonth:
    Next i

    Application.DisplayAlerts = True
    Application.ScreenUpdating = True
    If Len(report) = 0 Then report = "All months linked & verified successfully."
    MsgBox "Traceable summary built." & vbCrLf & vbCrLf & report, vbInformation
End Sub

Private Function NormU(v As Variant) As String
    Dim s As String: s = UCase(CStr(v))
    Dim ch As Variant
    For Each ch In Array(" ", "_", ".", "(", ")", "-", "/", vbLf, vbCr)
        s = Replace(s, CStr(ch), "")
    Next ch
    NormU = s
End Function

Private Function ValD(v As Variant) As Double
    If IsError(v) Then ValD = 0: Exit Function
    If IsNumeric(v) Then ValD = CDbl(v) Else ValD = 0
End Function

Private Function ColLetter(ByVal n As Long) As String
    Dim s As String
    Do While n > 0
        Dim r As Long: r = (n - 1) Mod 26
        s = Chr(65 + r) & s
        n = (n - 1) \ 26
    Loop
    ColLetter = s
End Function
