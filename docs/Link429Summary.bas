Attribute VB_Name = "Link429Summary"
'======================================================================
' Link429Summary  (v4 - fingerprint: match each figure by VALUE)
'
' The header named "REVISED_GROSS" in the monthly files does NOT equal the
' summary's gross (April is ~5x duplicated; others differ). So v4 stops
' trusting header names for the link target. For each month it:
'   1) opens the file, finds the data sheet + header row,
'   2) computes the SUM of EVERY column once,
'   3) for each figure already in your summary, finds the column whose
'      total MATCHES that figure, and links to it.
' Because your summary numbers are correct, this locates the real source
' column on its own - whatever it is named. Anything it can't reproduce is
' reported (so April's duplicated file is flagged, not silently mislinked).
'
' Auto-finds the summary sheet (tab "Monthly Summary", else "April" in col A,
' else ActiveSheet). Save a COPY as .xlsm in the SAME FOLDER as all 12
' monthly *_WITH_FORMULAE.xlsx files (rename any " - Copy"), then run.
'======================================================================
Option Explicit

Public Sub Link429Summary()
    Dim months As Variant
    months = Array("April", "May", "June", "July", "August", "September", _
                   "October", "November", "December", "January", "February", "March")
    ' summaryCol | label (used only for the report)
    Dim map As Variant
    map = Array("3|Revised Gross", "4|PF", "5|ESI", "6|PT", "7|LWF", "8|TDS", _
        "9|Emp Welfare Fund", "10|Advance", "11|Uniform", "12|Other Ded (entered)", _
        "13|Food Ded", "14|Food Deds", "15|Mobile Ded", "16|Professional Fees", _
        "17|Insurance Ded", "18|Insurance", "19|Fine", "20|Accomodation", "21|Flexi Ded", _
        "22|Conveyance Ded", "23|Laundry", "24|Meal Ded", "25|Refyne Adv", _
        "27|Other Ded (residual)", "29|Net Payable")

    Dim sumSh As Worksheet: Set sumSh = FindSummarySheet()
    If sumSh Is Nothing Then
        MsgBox "Could not find the summary sheet (the one with 'April' down column A).", vbExclamation
        Exit Sub
    End If

    Dim folder As String: folder = ThisWorkbook.Path & Application.PathSeparator
    Dim oldCalc As XlCalculation: oldCalc = Application.Calculation
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    Application.Calculation = xlCalculationManual
    Dim report As String, grandLinked As Long

    Dim i As Long, rowS As Long, fn As String, wb As Workbook
    For i = 0 To UBound(months)
        rowS = 5 + i
        fn = Dir(folder & months(i) & "*WITH_FORMULAE.xlsx")
        If fn = "" Then report = report & months(i) & ": FILE NOT FOUND" & vbCrLf: GoTo NextMonth

        Set wb = Workbooks.Open(folder & fn, ReadOnly:=True, UpdateLinks:=False)

        ' biggest sheet = data sheet
        Dim ws As Worksheet, s As Worksheet, best As Long
        best = 0: Set ws = Nothing
        For Each s In wb.Worksheets
            If s.UsedRange.Rows.Count > best Then best = s.UsedRange.Rows.Count: Set ws = s
        Next s

        Dim hr As Long, lastR As Long, maxC As Long
        maxC = ws.UsedRange.Column + ws.UsedRange.Columns.Count - 1
        If maxC < 1 Or maxC > 1000 Then maxC = 260
        lastR = ws.UsedRange.Row + ws.UsedRange.Rows.Count - 1
        hr = HeaderRowOf(ws, maxC)              ' row holding EMPCODE / REVISED*

        ' cache every column's data-sum once
        Dim csum() As Double: ReDim csum(1 To maxC)
        Dim c As Long
        For c = 1 To maxC
            csum(c) = Application.WorksheetFunction.Sum(ws.Range(ws.Cells(hr + 1, c), ws.Cells(lastR, c)))
        Next c

        Dim base As String: base = "'" & folder & "[" & fn & "]" & ws.Name & "'!"

        ' employee rows (count EMPCODE col if found by name)
        Dim ecCol As Long: ecCol = ColByName(ws, hr, maxC, "EMPCODE")
        If ecCol > 0 Then sumSh.Cells(rowS, 2).Value = _
            Application.WorksheetFunction.CountA(ws.Range(ws.Cells(hr + 1, ecCol), ws.Cells(lastR, ecCol)))

        ' link each figure by matching its value to a column total
        Dim p As Variant, parts() As String, scol As Long, lbl As String
        Dim cur As Double, tol As Double, found As Long, monthLinked As Long
        Dim hits As String, misses As String
        For Each p In map
            parts = Split(CStr(p), "|")
            scol = CLng(parts(0)): lbl = parts(1)
            cur = ValD(sumSh.Cells(rowS, scol))
            If Abs(cur) < 1 Then GoTo NextField        ' skip zero/blank (ambiguous)
            tol = Application.Max(50, Abs(cur) * 0.001)
            found = 0
            For c = 1 To maxC
                If Abs(csum(c) - cur) <= tol Then found = c: Exit For
            Next c
            If found > 0 Then
                sumSh.Cells(rowS, scol).Formula = "=SUM(" & base & "$" & ColLetter(found) & "$" & (hr + 1) & ":$" & ColLetter(found) & "$" & lastR & ")"
                sumSh.Cells(rowS, scol).NumberFormat = "#,##0"
                hits = hits & lbl & "=" & ColLetter(found) & " "
                monthLinked = monthLinked + 1: grandLinked = grandLinked + 1
            Else
                misses = misses & lbl & " "
            End If
NextField:
        Next p

        report = report & months(i) & ": linked " & monthLinked & "/25  (sheet '" & ws.Name & "', " & (lastR - hr) & " rows)" & vbCrLf
        If Len(hits) > 0 Then report = report & "    cols: " & hits & vbCrLf
        If Len(misses) > 0 Then report = report & "    NOT found in file: " & misses & vbCrLf

        wb.Close SaveChanges:=False
NextMonth:
    Next i

    Application.Calculation = oldCalc
    Application.Calculate
    Application.DisplayAlerts = True
    Application.ScreenUpdating = True
    MsgBox "Fingerprint linking finished. Total cells linked: " & grandLinked & vbCrLf & _
           "Summary sheet: '" & sumSh.Name & "'" & vbCrLf & vbCrLf & report, vbInformation
End Sub

' ---- helpers --------------------------------------------------------
Private Function HeaderRowOf(ws As Worksheet, ByVal maxC As Long) As Long
    Dim r As Long, c As Long, t As String
    For r = 1 To 20
        For c = 1 To maxC
            t = NormU(ws.Cells(r, c).Value)
            If t = "EMPCODE" Or t = "REVISED_GROSS" Or t = "REVISEDGROSS" Then HeaderRowOf = r: Exit Function
        Next c
    Next r
    HeaderRowOf = 1
End Function

Private Function ColByName(ws As Worksheet, ByVal hr As Long, ByVal maxC As Long, ByVal want As String) As Long
    Dim c As Long
    For c = 1 To maxC
        If NormU(ws.Cells(hr, c).Value) = want Then ColByName = c: Exit Function
    Next c
    ColByName = 0
End Function

Private Function FindSummarySheet() As Worksheet
    Dim sh As Worksheet, r As Long
    On Error Resume Next
    Set FindSummarySheet = ThisWorkbook.Sheets("Monthly Summary")
    On Error GoTo 0
    If Not FindSummarySheet Is Nothing Then Exit Function
    For Each sh In ThisWorkbook.Worksheets
        For r = 1 To 20
            If Trim(UCase(CStr(sh.Cells(r, 1).Value))) = "APRIL" Then Set FindSummarySheet = sh: Exit Function
        Next r
    Next sh
    If TypeName(ThisWorkbook.ActiveSheet) = "Worksheet" Then Set FindSummarySheet = ThisWorkbook.ActiveSheet
End Function

Private Function NormU(v As Variant) As String
    Dim s As String: s = UCase(CStr(v))
    Dim ch As Variant
    For Each ch In Array(" ", ".", "(", ")", "-", "/", vbLf, vbCr)
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
