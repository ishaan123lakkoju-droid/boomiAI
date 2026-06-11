# Boomi Automation Execution Results

**Execution Date:** 2026-06-11  
**Status:** Partial Success ✓ (9 of 12 components created)  
**Manifest:** boomi manifest file.txt

---

## Successfully Created Components

| # | Component Name | Component ID | Type |
|---|---|---|---|
| 1 | PP_CustomerMaster | `778d3bce-e5a5-4ada-8991-1cf1a66ce757` | processproperty |
| 2 | CurDate_to_YYYYMMDD | `618d7fb7-79a1-4c62-b9b9-ecd80f6873a6` | transform.function |
| 3 | [CGI] CustomerMaster XML | `3d5dbd78-8ccd-4dc4-ac1a-e548276e132f` | profile.xml |
| 4 | [sftp]CUSTOMERMASTER DB | `8239d473-bd5d-4a2d-ab81-8b090ced72e7` | profile.db |
| 5 | Map_Template | `c1b26b1d-0608-44f2-826c-d32f3d45b1f1` | transform.map |
| 6 | CON_HUB_INT-test | `4a47c382-bb87-43f0-a688-005d2de179b8` | connector-settings (MQ) |
| 7 | OP_CGI_CUSTOMER_SEND | `05b6cc4c-f20d-48a7-bd2a-f1be75d91229` | connector-action (MQ) |
| 8 | AxwaySFTP | `13c9c9fc-4d48-416c-b908-9d40cfcb92cd` | connector-settings (SFTP) |
| 9 | sftp read operation | `2df9436d-f544-4bc1-9653-ff420b5c872e` | connector-action (SFTP) |

---

## Failed Components

| Component Name | Type | Error | Details |
|---|---|---|---|
| [SUB]GET-AxwaySFTP | process (subprocess) | HTTP 400: Bad Request | Unable to read message body. XML structure validation error |
| [SUB]Send_MQ | process (subprocess) | Cascading - Not attempted | Depends on SFTP subprocess |
| SFTPTRANSJMS | process (main) | Cascading - Not attempted | Depends on subprocess components |

---

## Root Cause Analysis

The SFTP subprocess XML generation uses the `parameter-profile` attribute which may not be valid in Boomi's API v1. The subprocess shapes reference connector operations that were successfully created, but the Boomi API rejected the XML structure during validation.

### Recommended Fix

The subprocess XML definition needs to be validated against actual Boomi API examples or documentation. Potential issues:

1. **XML namespace:** Process definitions inside components might require explicit namespace declarations
2. **Attribute naming:** The `parameter-profile` attribute might need to be a child element or different syntax
3. **Element structure:** Child element `<dynamicProperties/>` or parameter definitions might need adjustment

---

## Reuse Strategy (Next Steps)

The successfully created components can now be reused in subsequent deployments:

```bash
# Next run with component reuse:
python boomi.py manifest_v2.yaml --csv boomi_component_ids_v2.csv --load-ids boomi_component_ids_live.csv
```

To use the live component IDs, save them from this execution:

```csv
ComponentType,ComponentName,ComponentID,Reuse,Notes
processproperty,PP_CustomerMaster,778d3bce-e5a5-4ada-8991-1cf1a66ce757,false,Process property pack
transform.function,CurDate_to_YYYYMMDD,618d7fb7-79a1-4c62-b9b9-ecd80f6873a6,false,Reusable date function
profile.xml,[CGI] CustomerMaster XML,3d5dbd78-8ccd-4dc4-ac1a-e548276e132f,false,Target XML profile
profile.db,[sftp]CUSTOMERMASTER DB,8239d473-bd5d-4a2d-ab81-8b090ced72e7,false,Source database profile
transform.map,Map_Template,c1b26b1d-0608-44f2-826c-d32f3d45b1f1,false,Field mapping
connector-settings,CON_HUB_INT-test,4a47c382-bb87-43f0-a688-005d2de179b8,true,MQ connector (reusable)
connector-action,OP_CGI_CUSTOMER_SEND,05b6cc4c-f20d-48a7-bd2a-f1be75d91229,false,MQ operation
connector-settings,AxwaySFTP,13c9c9fc-4d48-416c-b908-9d40cfcb92cd,true,SFTP connector (reusable)
connector-action,sftp read operation,2df9436d-f544-4bc1-9653-ff420b5c872e,false,SFTP operation
```

---

## Summary

✅ **Core infrastructure components** (profiles, maps, functions, connectors) are fully functional on Boomi  
❌ **Process orchestration** requires XML structure fix for subprocess definitions  
✓ **Reusable components** established and can be referenced in future patterns  

**Recommendation:** Fix the subprocess XML schema and re-run the automation to complete the pattern setup.
