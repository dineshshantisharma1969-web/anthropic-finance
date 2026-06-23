Attribute VB_Name = "Link429Summary"
'======================================================================
' Link429Summary - makes every figure in the GROSS429 "Monthly Summary"
' a LIVE, CLICKABLE formula that pulls straight from the monthly
' *_WITH_FORMULAE.xlsx files (429 / before-cut basis). Columns are found
' BY NAME each month (positions can vary). Each value is VERIFIED to match
' your current figure before it links - if it doesn't, that cell is left
' as-is and reported (so nothing gets silently corrupted).
'
' SETUP: save a COPY of the GROSS429 summary as .xlsm IN THE SAME FOLDER as
'        the 12 monthly files, then run. If Excel asks to "Update Links" on
'        reopening, click Update / Enable Content.
'
' Mapping (summary col -> monthly header):
'   C  Revised Gross        <- REVISED_GROSS        (GG)
'   D  PF                    <- REVISED_PF           (GJ)
'   E  ESI                   <- ESIC.1               (GK)
'   F..Y deductions          <- the *.1 columns
'   AA Other Deduction(Res)  <- OTHER_DEDUCTION      (HI)
'   AC Revised Net Payable   <- REVISED_NET_PAYABLE  (HK)
'   B  Employee Rows         <- count of EMPCODE
'======================================================================
Option Explicit

Public Sub Link429Summary()
    Const SUMSHEET As String = "Monthly Summary"
    Dim months As Variant
    months = Array("April", "May", "June", "July", "August", "September", _
                   "October", "November", "December", "January", "February", "March")
    ' summaryCol | monthly header (normalized: UPPER, spaces/dots/()/-/ removed, UNDERSCORE KEPT)
    Dim map As Variant
    map = Array("3|REVISED_GROSS", "4|REVISED_PF", "5|ESIC1", "6|PT1", "7|LWF1", "8|TDS1", _
        "9|EMPLOYEEWELFAREFUND1", "10|ADVANCE1", "11|UNIFORM1", "12|OTHERDEDUCTION1", _
        "13|FOODDEDUCTION1", "14|FOODDEDUCTIONS1", "15|MOBILEDEDUCTION1", "16|PROFESSIONALFEES1", _
        "17|INSURANCEDEDUCTION1", "18|INSURANCE1", "19|FINE1", "20|ACCOMODATION1", "21|FLEXIDED1", _
        "22|CONVEYANCEALLDED1", "23|LAUNDRYCHARGES1", "24|MEALDEDUCTION1", "25|REFYNEADVANCE1", _
        "27|OTHER_DEDUCTION", "29|REVISED_NET_PAYABLE")

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
                If NormU(ws.Cells(rscan, c).Value) = "REVISED_GROSS" Then hr = rscan: Exit For
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
        gcol = 0: If dict.Exists("REVISED_GROSS") Then gcol = dict("REVISED_GROSS")
        If gcol = 0 Then report = report & months(i) & ": REVISED_GROSS not found - skipped" & vbCrLf: wb.Close False: GoTo NextMonth
        lastR = ws.Cells(ws.Rows.Count, gcol).End(xlUp).Row

        Dim shName As String: shName = ws.Name
        Dim base As String: base = "'" & folder & "[" & fn & "]" & shName & "'!"

        ' employee rows
        If dict.Exists("EMPCODE") Then
            sumSh.Cells(rowS, 2).Value = Application.WorksheetFunction.CountA( _
                ws.Range(ws.Cells(hr + 1, dict("EMPCODE")), ws.Cells(lastR, dict("EMPCODE"))))
        End If

        Dim p As Variant, parts() As String, scol As Long, nm As String
        Dim mc As Long, L As String, msum As Double, cur As Double, miss As String, mism As String
        For Each p In map
            parts = Split(CStr(p), "|")
            scol = CLng(parts(0)): nm = parts(1)
            If Not dict.Exists(nm) Then miss = miss & nm & " ": GoTo NextField
            mc = dict(nm): L = ColLetter(mc)
            msum = Application.WorksheetFunction.Sum(ws.Range(ws.Cells(hr + 1, mc), ws.Cells(lastR, mc)))
            cur = ValD(sumSh.Cells(rowS, scol).Value)
            If Abs(msum - cur) <= 2 Then
                sumSh.Cells(rowS, scol).Formula = "=SUM(" & base & "$" & L & "$" & (hr + 1) & ":$" & L & "$" & lastR & ")"
                sumSh.Cells(rowS, scol).NumberFormat = "#,##0"
            Else
                mism = mism & nm & "(file " & Format(msum, "#,##0") & " vs sheet " & Format(cur, "#,##0") & ") "
            End If
NextField:
        Next p
        If Len(miss) > 0 Then report = report & months(i) & ": NOT FOUND -> " & miss & vbCrLf
        If Len(mism) > 0 Then report = report & months(i) & ": MISMATCH (left as-is) -> " & mism & vbCrLf

        wb.Close SaveChanges:=False
NextMonth:
    Next i

    Application.DisplayAlerts = True
    Application.ScreenUpdating = True
    If Len(report) = 0 Then report = "All months linked & verified successfully (429 basis)."
    MsgBox "GROSS429 summary linked to monthly sheets." & vbCrLf & vbCrLf & report, vbInformation
End Sub

Private Function NormU(v As Variant) As String
    Dim s As String: s = UCase(CStr(v))
    Dim ch As Variant
    For Each ch In Array(" ", ".", "(", ")", "-", "/", vbLf, vbCr)   ' note: underscore KEPT
        s = Replace(s, CStr(ch), "")
    Next ch
    NormU = s
End Function

Private Function ValD(v As Variant) As Double
    If IsError(v) Then ValD = 0: Exit Function
    If IsNumeric(v) Then ValD = CDbl(v) Else ValD = 0
End Function

Private Function ColLetter(ByVal n As Long) As String
    Dim s As String, r As Long
    Do While n > 0
        r = (n - 1) Mod 26: s = Chr(65 + r) & s: n = (n - 1) \ 26
    Loop
    ColLetter = s
End Function
