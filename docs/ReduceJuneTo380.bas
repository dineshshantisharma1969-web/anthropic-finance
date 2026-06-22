Attribute VB_Name = "ReduceJuneTo380"
'======================================================================
' ReduceJuneTo380  -  June FY2025-26 "reduce Revised Gross to 380cr" pass
'----------------------------------------------------------------------
' Reduces REVISED ATTENDANCE ALLOWANCE (col 188) so REVISED GROSS (189)
' comes down to Rs 29,89,50,541; OTHER DEDUCTION (col 212) absorbs the
' SAME amount; REVISED TOTAL DED (217) reduced too; NET PAYABLE (218),
' PF, ESI, BASIC, DA all UNCHANGED.  Covered rows first (gross <= 21000),
' then exempt (gross > 21000, never taken below the 21000 ceiling).
' OTHER DEDUCTION never goes negative; attendance allowance never < 0.
'
' HOW TO RUN:
'   1. Open June_WITH_FORMULAE.xlsx in Excel
'   2. Press Alt+F11  (VBA editor) -> Insert > Module -> paste this
'   3. Press F5 (Run).  Read the message box.
'   4. Save the workbook (keep .xlsx).  Summary then ties to 380.00 cr.
'======================================================================
Option Explicit

Public Sub ReduceJuneTo380()
    Dim TARGET As Double: TARGET = 298950541#   ' Rs 29,89,50,541
    Dim FLOORv As Double: FLOORv = 21000#       ' ESI-exempt gross floor
    Dim ws As Worksheet, s As Worksheet, best As Long

    ' pick the sheet with the most rows (the salary data sheet)
    For Each s In ThisWorkbook.Worksheets
        If s.UsedRange.Rows.Count > best Then best = s.UsedRange.Rows.Count: Set ws = s
    Next s
    ' To force a specific sheet instead, uncomment & edit:
    ' Set ws = ThisWorkbook.Sheets("Sheet1")

    Dim hr As Long
    hr = FindHeaderRow(ws)
    If hr = 0 Then hr = 3                        ' skill default header row

    Dim cGF As Long, cGG As Long, cOD As Long, cHI As Long, cHJ As Long
    cGF = ColByName(ws, hr, Array("REVISED ATTENDANCE ALLOWANCE", "REVISED_ATTENDANCE_ALLOWANCE"), 188)
    cGG = ColByName(ws, hr, Array("REVISED GROSS", "REVISED_GROSS"), 189)
    cOD = ColByName(ws, hr, Array("REVISED OTHER DEDUCTION", "OTHER DEDUCTION"), 212)
    cHI = ColByName(ws, hr, Array("REVISED TOTAL DED", "REVISED_TOTAL_DED", "REVISED TOTAL DEDUCTION"), 217)
    cHJ = ColByName(ws, hr, Array("REVISED NET PAYABLE", "REVISED_NET_PAYABLE", "NETPAYABLE"), 218)

    Dim lastRow As Long
    lastRow = ws.Cells(ws.Rows.Count, cGG).End(xlUp).Row

    Dim r As Long, curTotal As Double, netTotal As Double
    For r = hr + 1 To lastRow
        curTotal = curTotal + V0(ws.Cells(r, cGG).Value)
        netTotal = netTotal + V0(ws.Cells(r, cHJ).Value)
    Next r

    Dim R As Double: R = curTotal - TARGET
    If R <= 0 Then
        MsgBox "Nothing to reduce. Current gross = " & Format(curTotal, "#,##0"), vbInformation
        Exit Sub
    End If

    Application.Calculation = xlCalculationManual
    Application.ScreenUpdating = False

    Dim pass As Integer, gf As Double, gg As Double, od As Double, hi As Double
    Dim isExempt As Boolean, cap As Double, d As Double, remaining As Double
    remaining = R
    For pass = 1 To 2                             ' 1 = covered, 2 = exempt
        For r = hr + 1 To lastRow
            If remaining <= 0 Then Exit For
            gg = V0(ws.Cells(r, cGG).Value)
            If gg <> 0 Then
                isExempt = (gg > FLOORv)
                If (pass = 1 And Not isExempt) Or (pass = 2 And isExempt) Then
                    gf = V0(ws.Cells(r, cGF).Value)
                    od = V0(ws.Cells(r, cOD).Value)
                    cap = od
                    If gf < cap Then cap = gf
                    If isExempt Then
                        If (gg - FLOORv) < cap Then cap = gg - FLOORv
                    End If
                    If cap < 0 Then cap = 0
                    d = remaining
                    If cap < d Then d = cap
                    If d > 0 Then
                        hi = V0(ws.Cells(r, cHI).Value)
                        ws.Cells(r, cGF).Value = Round(gf - d, 2)
                        ws.Cells(r, cOD).Value = Round(od - d, 2)
                        If Not ws.Cells(r, cHI).HasFormula Then ws.Cells(r, cHI).Value = Round(hi - d, 2)
                        If Not ws.Cells(r, cGG).HasFormula Then ws.Cells(r, cGG).Value = Round(gg - d, 2)
                        ' NET (cHJ) deliberately NOT changed
                        remaining = remaining - d
                    End If
                End If
            End If
        Next r
    Next pass

    Application.Calculation = xlCalculationAutomatic
    Application.ScreenUpdating = True

    Dim newTotal As Double: newTotal = curTotal - (R - remaining)
    Dim m As String
    m = "JUNE reduction done." & vbCrLf & vbCrLf
    m = m & "Header row: " & hr & "   Cols: GF=" & cGF & " GG=" & cGG & " OD=" & cOD & " TotDed=" & cHI & " Net=" & cHJ & vbCrLf & vbCrLf
    m = m & "Old gross : " & Format(curTotal, "#,##0") & vbCrLf
    m = m & "Target    : " & Format(TARGET, "#,##0") & vbCrLf
    m = m & "New gross : " & Format(newTotal, "#,##0") & vbCrLf
    m = m & "Net total : " & Format(netTotal, "#,##0") & "  (unchanged)"
    If remaining > 1 Then
        m = m & vbCrLf & vbCrLf & "WARNING: Rs " & Format(remaining, "#,##0") & " could NOT be allocated (capacity limit). Review before saving."
        MsgBox m, vbExclamation
    Else
        m = m & vbCrLf & vbCrLf & "Save the file (keep .xlsx). Summary will tie to 380.00 cr."
        MsgBox m, vbInformation
    End If
End Sub

Private Function V0(v As Variant) As Double
    If IsError(v) Then V0 = 0: Exit Function
    If IsNumeric(v) Then V0 = CDbl(v) Else V0 = 0
End Function

Private Function NormU(v As Variant) As String
    Dim s As String: s = UCase(CStr(v))
    s = Replace(s, " ", ""): s = Replace(s, "_", "")
    NormU = s
End Function

Private Function FindHeaderRow(ws As Worksheet) As Long
    Dim r As Long, c As Long, t As String, hits As Integer, lc As Long
    lc = ws.UsedRange.Columns.Count
    For r = 1 To 15
        hits = 0
        For c = 1 To lc
            t = NormU(ws.Cells(r, c).Value)
            If t = "REVISEDGROSS" Or t = "REVISEDATTENDANCEALLOWANCE" _
               Or t = "REVISEDNETPAYABLE" Or t = "REVISEDOTHERDEDUCTION" Then hits = hits + 1
        Next c
        If hits >= 2 Then FindHeaderRow = r: Exit Function
    Next r
    FindHeaderRow = 0
End Function

Private Function ColByName(ws As Worksheet, hr As Long, names As Variant, fallback As Long) As Long
    Dim c As Long, i As Long, t As String, lc As Long
    lc = ws.UsedRange.Columns.Count
    For c = 1 To lc
        t = NormU(ws.Cells(hr, c).Value)
        For i = LBound(names) To UBound(names)
            If t = NormU(names(i)) Then ColByName = c: Exit Function
        Next i
    Next c
    ColByName = fallback
End Function
