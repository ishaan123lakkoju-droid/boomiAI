#!/usr/bin/env python3
"""
boomi.py
========

A manifest-driven Boomi automation helper.

This script creates Boomi components from a YAML manifest and stores the
created component IDs in CSV form for reusable automation.

Usage:
  python boomi.py manifest.yaml --csv boomi_component_ids.csv [--dry-run]

Requirements:
  pip install pyyaml
"""

import base64
import csv
import os
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

try:
    import yaml
except ImportError:
    yaml = None

DEFAULT_ACCOUNT_ID = "techmahindranfrmaster-4WVRJM"
DEFAULT_USERNAME = "BOOMI_TOKEN.UK00887178@techmahindra.com"
DEFAULT_TOKEN = "2701f430-5db8-4f98-9fbf-ce9b4fefc579"


def load_manifest(path):
    if yaml is None:
        raise SystemExit("PyYAML is required. Install with: pip install pyyaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class BoomiClient:
    def __init__(self, account_id=None, username=None, token=None, base_url=None):
        self.account_id = account_id or os.getenv("BOOMI_ACCOUNT_ID") or DEFAULT_ACCOUNT_ID
        self.username = username or os.getenv("BOOMI_USERNAME") or DEFAULT_USERNAME
        self.token = token or os.getenv("BOOMI_TOKEN") or DEFAULT_TOKEN
        self.base_url = base_url or os.getenv("BOOMI_BASE_URL") or f"https://api.boomi.com/api/rest/v1/{self.account_id}/Component"

    def auth_header(self):
        auth = f"{self.username}:{self.token}"
        return "Basic " + base64.b64encode(auth.encode("utf-8")).decode("utf-8")

    def create_component(self, xml_body, dry_run=False):
        if dry_run:
            fake_id = f"dryrun-{abs(hash(xml_body)) % 10_000_000}"
            return fake_id

        request = urllib.request.Request(
            self.base_url,
            data=xml_body.encode("utf-8"),
            headers={
                "Authorization": self.auth_header(),
                "Content-Type": "application/xml",
                "Accept": "application/xml",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request) as response:
                body = response.read().decode("utf-8")
                xml = ET.fromstring(body)
                return xml.attrib.get("componentId")
        except urllib.error.HTTPError as exc:
            message = exc.read().decode("utf-8")
            raise RuntimeError(f"Boomi API error {exc.code}: {message}") from exc

    def create_or_reuse(self, label, xml_body, existing_id=None, dry_run=False):
        if existing_id:
            print(f"  -> {label} [REUSE] {existing_id}")
            return existing_id
        print(f"  -> {label}")
        cid = self.create_component(xml_body, dry_run=dry_run)
        print(f"     created {cid}")
        return cid

    def save_ids_csv(self, ids, csv_path):
        fieldnames = ["ComponentType", "ComponentName", "ComponentID", "Reuse", "Notes"]
        with open(csv_path, "w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for comp in ids:
                writer.writerow(comp)


def load_existing_ids(csv_path):
    if not csv_path or not os.path.exists(csv_path):
        return {}
    with open(csv_path, encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        return {
            row["ComponentName"]: row["ComponentID"]
            for row in reader
            if row.get("ComponentName") and row.get("ComponentID")
        }


def wrap_component(name, comp_type, inner, folder_id="", sub="", desc=""):
    sub_attr = f' subType="{sub}"' if sub else ""
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<bns:Component xmlns:bns="http://api.platform.boomi.com/" '
        f'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        f'name="{name}" type="{comp_type}"{sub_attr} folderId="{folder_id}">'
        f'<bns:encryptedValues/><bns:description>{desc}</bns:description>'
        f'<bns:object>{inner}</bns:object>'
        f'</bns:Component>'
    )


def build_process_property(manifest, folder_id=""):
    pp = manifest["process_properties"]
    values = pp["values"]

    def prop(key, label, default, allowed=""):
        allowed_tag = f"<allowedValues>{allowed}</allowedValues>" if allowed else "<allowedValues/>"
        return (
            f'<definedProcessProperty key="{key}">'
            f'<helpText/><label>{label}</label><type>string</type>'
            f'<defaultValue>{default}</defaultValue>{allowed_tag}'
            f'<persisted>false</persisted></definedProcessProperty>'
        )

    inner = "<DefinedProcessProperties>"
    inner += prop("346725d9-ae91-4b20-b0b8-76051ef2c63c", "DestinationID", values.get("DestinationID", ""))
    inner += prop("4581226a-338b-4ee8-83a2-c4a602ca37cd", "SenderID", values.get("SenderID", ""))
    inner += prop("87d4f770-3060-4aa0-8550-bc5ef83578c9", "OperationOrganizationID", values.get("OperationOrganizationID", ""))
    inner += prop("eac70b0d-3b93-4685-9324-54e2e642352d", "MessageType", values.get("MessageType", ""))
    inner += prop("d62a1934-ad1c-4cd1-a19a-ca1e6e816269", "MessageID", values.get("MessageID", ""))
    inner += prop("4d0fc5a7-4586-4742-8350-71398705ff66", "AdviceMethod", values.get("AdviceMethod", ""))
    inner += prop("b4487562-d28b-4845-915e-eb3934275b30", "CustomerType", values.get("CustomerType", ""))
    inner += prop(
        "95274e69-53a8-45dd-a3cb-e24389eb217f", "RebateIndicator", values.get("RebateIndicator", "Y"),
        '<allowedValueSet label="Y" value="Y"/><allowedValueSet label="N" value="N"/>'
    )
    inner += prop(
        "f44dac41-ffa5-4d65-a3a4-0561b67448cf", "InitialChange", values.get("InitialChange", "A"),
        '<allowedValueSet label="A" value="A"/><allowedValueSet label="C" value="C"/>'
    )
    inner += prop("dcb5c357-caca-471d-9035-58f7398403fc", "CustomerEntryType", values.get("CustomerEntryType", ""))
    inner += prop("a210517e-25df-4e85-94ef-ea862d9efca0", "Attachment", values.get("Attachment", "N"))
    inner += prop("ceca7db8-4b06-45f3-acb8-ab2b8fb882bb", "Integration_Type", values.get("Integration_Type", ""))
    inner += prop("73cd4b9b-67b6-4e9f-97de-9505b0c6d76a", "Severity", values.get("Severity", ""))
    inner += prop("b72e06d0-dd4a-4563-a4dc-60d98c06a48a", "Payload", values.get("Payload", ""))
    inner += prop("dce5ed88-b8b3-4b5c-afd2-34e7f6d4c896", "FileName", values.get("FileName", ""))
    inner += prop("2d39d9f4-2d67-4ec1-bbb5-20191b945422", "AlertNotification", values.get("AlertNotification", "Y"))
    inner += prop("b2a42a53-c311-47dc-b53a-c45141e66542", "EnvironmentName", values.get("EnvironmentName", ""))
    inner += prop("5de8796b-25e6-403a-b990-e3279f91d50d", "FromEmail", values.get("FromEmail", ""))
    inner += prop("c65b8248-3d37-4c02-a8a1-2bd9818e4a91", "ToEmail1", values.get("ToEmail1", ""))
    inner += prop("ef12a557-676a-49eb-a0d1-1dbbf1668e58", "Source System", values.get("Source_System", ""))
    inner += prop("efa0cf37-c4fd-4b7f-9c7f-c102996ce71c", "Target System", values.get("Target_System", ""))
    inner += "</DefinedProcessProperties>"

    return wrap_component(pp["name"], "processproperty", inner, folder_id)


def build_map_function(manifest, folder_id=""):
    name = manifest["map_function"]["name"]
    inner = """
<Function>
  <Inputs><Input key="1" name="A"/></Inputs>
  <Outputs><Output key="1" name="B"/><Output key="2" name="C"/></Outputs>
  <Steps>
    <FunctionStep cacheEnabled="true" category="Date" key="1" name="Get Current Date" position="1" sumEnabled="false" type="CurrentDate" x="2.0" y="139.0"><Inputs/><Outputs><Output key="2" name="Result"/></Outputs><Configuration/></FunctionStep>
    <FunctionStep cacheEnabled="true" cacheOption="none" category="Date" key="2" name="Date Format" position="3" sumEnabled="false" type="DateFormat" x="100.0" y="268.0"><Inputs><Input key="1" name="Date String"/><Input default="yyyyMMdd HHmmss.SSS" key="2" name="Input Mask"/><Input default="yyyyMMdd" key="3" name="Output Mask"/></Inputs><Outputs><Output key="2" name="Result"/></Outputs><Configuration/></FunctionStep>
    <FunctionStep cacheEnabled="true" cacheOption="none" category="Date" key="3" name="Date Format" position="2" sumEnabled="false" type="DateFormat" x="90.0" y="402.0"><Inputs><Input key="1" name="Date String"/><Input default="yyyyMMdd HHmmss.SSS" key="2" name="Input Mask"/><Input default="HHmm" key="3" name="Output Mask"/></Inputs><Outputs><Output key="2" name="Result"/></Outputs><Configuration/></FunctionStep>
  </Steps>
  <Mappings>
    <Mapping fromFunction="1" fromKey="2" fromType="function" toFunction="2" toKey="1" toType="function"/>
    <Mapping fromFunction="1" fromKey="2" fromType="function" toFunction="3" toKey="1" toType="function"/>
    <Mapping fromFunction="2" fromKey="2" fromType="function" toFunction="0" toKey="1" toType="function"/>
    <Mapping fromFunction="3" fromKey="2" fromType="function" toFunction="0" toKey="2" toType="function"/>
  </Mappings>
</Function>"""
    return wrap_component(name, "transform.function", inner, folder_id)


def build_target_profile(manifest, folder_id=""):
    name = manifest["target_profile"]["name"]
    inner = """
<XMLProfile modelVersion="2" strict="true">
  <ProfileProperties>
    <XMLGeneralInfo/>
    <XMLOptions encoding="utf8" implicitElementOrdering="true" parseRespectMaxOccurs="true" respectMinOccurs="false" respectMinOccursAlways="false"/>
  </ProfileProperties>
  <DataElements>
    <XMLElement dataType="character" isMappable="true" isNode="true" key="1" maxOccurs="1" minOccurs="1" name="Proponix" useNamespace="-1">
      <DataFormat><ProfileCharacterFormat/></DataFormat>
      <XMLElement dataType="character" isMappable="true" isNode="true" key="2" maxOccurs="1" minOccurs="0" name="Header" useNamespace="-1">
        <DataFormat><ProfileCharacterFormat/></DataFormat>
        <XMLElement key="3" name="DestinationID" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
        <XMLElement key="4" name="SenderID" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
        <XMLElement key="5" name="OperationOrganizationID" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
        <XMLElement key="6" name="MessageType" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
        <XMLElement key="7" name="DateSent" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
        <XMLElement key="8" name="TimeSent" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
        <XMLElement key="9" name="MessageID" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
      </XMLElement>
      <XMLElement dataType="character" isMappable="true" isNode="true" key="10" maxOccurs="1" minOccurs="0" name="SubHeader" useNamespace="-1" validateData="false">
        <DataFormat><ProfileCharacterFormat/></DataFormat><QualifierList/>
        <XMLElement key="11" name="CustomerID" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0" validateData="false"><DataFormat><ProfileCharacterFormat/></DataFormat><QualifierList/></XMLElement>
        <XMLElement key="72" name="CustomerName" useNamespace="-1" dataType="character" isMappable="true" isNode="true" loopingOption="unique" maxOccurs="1" minOccurs="0" validateData="false"><DataFormat><ProfileCharacterFormat/></DataFormat><QualifierList/></XMLElement>
        <XMLElement key="73" name="ShortName" useNamespace="-1" dataType="character" isMappable="true" isNode="true" loopingOption="unique" maxOccurs="1" minOccurs="0" validateData="false"><DataFormat><ProfileCharacterFormat/></DataFormat><QualifierList/></XMLElement>
        <XMLElement key="12" name="InitialChange" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
        <XMLElement key="13" name="CentralCustomerID" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
      </XMLElement>
      <XMLElement dataType="character" isMappable="true" isNode="true" key="14" maxOccurs="1" minOccurs="0" name="Body" useNamespace="-1">
        <DataFormat><ProfileCharacterFormat/></DataFormat>
        <XMLElement dataType="character" isMappable="true" isNode="true" key="15" maxOccurs="1" minOccurs="0" name="CustomerInformation" useNamespace="-1">
          <DataFormat><ProfileCharacterFormat/></DataFormat>
          <XMLElement key="19" name="Country" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
          <XMLElement key="20" name="CountryNationality" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
          <XMLElement key="21" name="CountryRisk" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
          <XMLElement key="22" name="CustomerEntryType" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
          <XMLElement key="23" name="CustomerEntryID" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
          <XMLElement key="24" name="CustomerType" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
          <XMLElement key="30" name="PrimaryLanguage" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
          <XMLElement key="31" name="RebateIndicator" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
          <XMLElement key="54" name="ServicingBranch" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
          <XMLElement key="36" name="UserDefinedField1" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
          <XMLElement key="37" name="UserDefinedField2" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
          <XMLElement key="38" name="UserDefinedField3" useNamespace="-1" dataType="character" isMappable="true" isNode="true" maxOccurs="1" minOccurs="0"><DataFormat><ProfileCharacterFormat/></DataFormat></XMLElement>
        </XMLElement>
      </XMLElement>
    </XMLElement>
  </DataElements>
  <Namespaces><XMLNamespace key="-1" name="Empty Namespace"><Types/></XMLNamespace></Namespaces>
  <tagLists/>
</XMLProfile>"""
    return wrap_component(name, "profile.xml", inner, folder_id)


def build_source_profile(manifest, folder_id=""):
    sp = manifest["source_profile"]
    sql = sp["sql"].strip().replace("\n", " ")
    inner = f"""
<DatabaseProfile strict="true" version="2">
  <ProfileProperties><DatabaseGeneralInfo executionType="dbread"/></ProfileProperties>
  <DataElements>
    <DBStatement isNode="true" key="2" name="Statement" statementType="select" storedProcedure="" tableName="">
      <DBFields isNode="true" key="3" name="Fields" type="result_set">
        <DatabaseElement dataType="character" enforceUnique="false" isMappable="true" isNode="true" key="18" mandatory="false" name="address_5"><DataFormat><ProfileCharacterFormat/></DataFormat></DatabaseElement>
        <DatabaseElement dataType="character" enforceUnique="false" isMappable="true" isNode="true" key="19" mandatory="false" name="booking_office"><DataFormat><ProfileCharacterFormat/></DataFormat></DatabaseElement>
        <DatabaseElement dataType="character" enforceUnique="false" isMappable="true" isNode="true" key="20" mandatory="false" name="ccif_no"><DataFormat><ProfileCharacterFormat/></DataFormat></DatabaseElement>
        <DatabaseElement dataType="character" enforceUnique="false" isMappable="true" isNode="true" key="21" mandatory="false" name="control_office"><DataFormat><ProfileCharacterFormat/></DataFormat></DatabaseElement>
        <DatabaseElement dataType="character" enforceUnique="false" isMappable="true" isNode="true" key="22" mandatory="false" name="core_info_control_office"><DataFormat><ProfileCharacterFormat/></DataFormat></DatabaseElement>
        <DatabaseElement dataType="character" enforceUnique="false" isMappable="true" isNode="true" key="26" mandatory="false" name="crnt_profit_center1"><DataFormat><ProfileCharacterFormat/></DataFormat></DatabaseElement>
        <DatabaseElement dataType="character" enforceUnique="false" isMappable="true" isNode="true" key="27" mandatory="false" name="crnt_profit_center2"><DataFormat><ProfileCharacterFormat/></DataFormat></DatabaseElement>
        <DatabaseElement dataType="character" enforceUnique="false" isMappable="true" isNode="true" key="28" mandatory="false" name="crnt_profit_center3"><DataFormat><ProfileCharacterFormat/></DataFormat></DatabaseElement>
        <DatabaseElement dataType="character" enforceUnique="false" isMappable="true" isNode="true" key="29" mandatory="false" name="cust_full_name"><DataFormat><ProfileCharacterFormat/></DataFormat></DatabaseElement>
        <DatabaseElement dataType="character" enforceUnique="false" isMappable="true" isNode="true" key="34" mandatory="false" name="cust_type"><DataFormat><ProfileCharacterFormat/></DataFormat></DatabaseElement>
        <DatabaseElement dataType="character" enforceUnique="false" isMappable="true" isNode="true" key="36" mandatory="false" name="gcif_no"><DataFormat><ProfileCharacterFormat/></DataFormat></DatabaseElement>
        <DatabaseElement dataType="character" enforceUnique="false" isMappable="true" isNode="true" key="53" mandatory="false" name="mizuho_ccif_no"><DataFormat><ProfileCharacterFormat/></DataFormat></DatabaseElement>
        <DatabaseElement dataType="character" enforceUnique="false" isMappable="true" isNode="true" key="57" mandatory="false" name="resident_type"><DataFormat><ProfileCharacterFormat/></DataFormat></DatabaseElement>
        <DatabaseElement dataType="character" enforceUnique="false" isMappable="true" isNode="true" key="58" mandatory="false" name="swift_branch_code"><DataFormat><ProfileCharacterFormat/></DataFormat></DatabaseElement>
        <DatabaseElement dataType="character" enforceUnique="false" isMappable="true" isNode="true" key="67" mandatory="false" name="lc_idf_gur_type"><DataFormat><ProfileCharacterFormat/></DataFormat></DatabaseElement>
        <DatabaseElement dataType="character" enforceUnique="false" isMappable="true" isNode="true" key="68" mandatory="false" name="local_language"><DataFormat><ProfileCharacterFormat/></DataFormat></DatabaseElement>
        <DatabaseElement dataType="character" enforceUnique="false" isMappable="true" isNode="true" key="69" mandatory="false" name="profit_owner_mizuho_ccif_no"><DataFormat><ProfileCharacterFormat/></DataFormat></DatabaseElement>
        <DatabaseElement enforceUnique="false" isMappable="true" isNode="true" key="70" mandatory="false" name="UUID"><DataFormat><ProfileCharacterFormat/></DataFormat></DatabaseElement>
      </DBFields>
      <DBParameters isNode="true" key="4" name="Parameters"/>
      <sql>{sql}</sql>
    </DBStatement>
  </DataElements>
</DatabaseProfile>"""
    return wrap_component(sp["name"], "profile.db", inner, folder_id)


def build_map(manifest, folder_id, pp_id, src_id, tgt_id, mapfn_id):
    pp_name = manifest["process_properties"]["name"]
    name = manifest["map"]["name"]
    inner = f"""
<Map fromProfile="{src_id}" toProfile="{tgt_id}">
  <Mappings>
    <Mapping fromKey="36" fromKeyPath="*[@key='2']/*[@key='3']/*[@key='36']" fromNamePath="Statement/Fields/gcif_no" fromType="profile" toKey="11" toKeyPath="*[@key='1']/*[@key='10']/*[@key='11']" toNamePath="Proponix/SubHeader/CustomerID" toType="profile"/>
    <Mapping fromKey="53" fromKeyPath="*[@key='2']/*[@key='3']/*[@key='53']" fromNamePath="Statement/Fields/mizuho_ccif_no" fromType="profile" toKey="13" toKeyPath="*[@key='1']/*[@key='10']/*[@key='13']" toNamePath="Proponix/SubHeader/CentralCustomerID" toType="profile"/>
    <Mapping fromKey="29" fromKeyPath="*[@key='2']/*[@key='3']/*[@key='29']" fromNamePath="Statement/Fields/cust_full_name" fromType="profile" toKey="72" toKeyPath="*[@key='1']/*[@key='10']/*[@key='72']" toNamePath="Proponix/SubHeader/CustomerName" toType="profile"/>
    <Mapping fromFunction="1" fromKey="1" fromType="function" toKey="3" toKeyPath="*[@key='1']/*[@key='2']/*[@key='3']" toNamePath="Proponix/Header/DestinationID" toType="profile"/>
    <Mapping fromFunction="2" fromKey="1" fromType="function" toKey="4" toKeyPath="*[@key='1']/*[@key='2']/*[@key='4']" toNamePath="Proponix/Header/SenderID" toType="profile"/>
    <Mapping fromFunction="3" fromKey="1" fromType="function" toKey="5" toKeyPath="*[@key='1']/*[@key='2']/*[@key='5']" toNamePath="Proponix/Header/OperationOrganizationID" toType="profile"/>
    <Mapping fromFunction="4" fromKey="1" fromType="function" toKey="6" toKeyPath="*[@key='1']/*[@key='2']/*[@key='6']" toNamePath="Proponix/Header/MessageType" toType="profile"/>
    <Mapping fromFunction="10" fromKey="1" fromType="function" toKey="7" toKeyPath="*[@key='1']/*[@key='2']/*[@key='7']" toNamePath="Proponix/Header/DateSent" toType="profile"/>
    <Mapping fromFunction="10" fromKey="2" fromType="function" toKey="8" toKeyPath="*[@key='1']/*[@key='2']/*[@key='8']" toNamePath="Proponix/Header/TimeSent" toType="profile"/>
    <Mapping fromFunction="5" fromKey="1" fromType="function" toKey="31" toKeyPath="*[@key='1']/*[@key='14']/*[@key='15']/*[@key='31']" toNamePath="Proponix/Body/CustomerInformation/RebateIndicator" toType="profile"/>
    <Mapping fromFunction="11" fromKey="1" fromType="function" toKey="12" toKeyPath="*[@key='1']/*[@key='10']/*[@key='12']" toNamePath="Proponix/SubHeader/InitialChange" toType="profile"/>
    <Mapping fromFunction="12" fromKey="1" fromType="function" toKey="22" toKeyPath="*[@key='1']/*[@key='14']/*[@key='15']/*[@key='22']" toNamePath="Proponix/Body/CustomerInformation/CustomerEntryType" toType="profile"/>
    <Mapping fromKey="34" fromKeyPath="*[@key='2']/*[@key='3']/*[@key='34']" fromNamePath="Statement/Fields/cust_type" fromType="profile" toKey="24" toKeyPath="*[@key='1']/*[@key='14']/*[@key='15']/*[@key='24']" toNamePath="Proponix/Body/CustomerInformation/CustomerType" toType="profile"/>
    <Mapping fromKey="58" fromKeyPath="*[@key='2']/*[@key='3']/*[@key='58']" fromNamePath="Statement/Fields/swift_branch_code" fromType="profile" toKey="54" toKeyPath="*[@key='1']/*[@key='14']/*[@key='15']/*[@key='54']" toNamePath="Proponix/Body/CustomerInformation/ServicingBranch" toType="profile"/>
    <Mapping fromKey="20" fromKeyPath="*[@key='2']/*[@key='3']/*[@key='20']" fromNamePath="Statement/Fields/ccif_no" fromType="profile" toKey="23" toKeyPath="*[@key='1']/*[@key='14']/*[@key='15']/*[@key='23']" toNamePath="Proponix/Body/CustomerInformation/CustomerEntryID" toType="profile"/>
    <Mapping fromKey="18" fromKeyPath="*[@key='2']/*[@key='3']/*[@key='18']" fromNamePath="Statement/Fields/address_5" fromType="profile" toKey="19" toKeyPath="*[@key='1']/*[@key='14']/*[@key='15']/*[@key='19']" toNamePath="Proponix/Body/CustomerInformation/Country" toType="profile"/>
  </Mappings>
  <Functions optimizeExecutionOrder="true">
    <FunctionStep cacheEnabled="true" category="ProcessProperty" key="1" name="Get Process Property" position="1" sumEnabled="false" type="DefinedProcessPropertyGet" x="10.0" y="10.0"><Inputs/><Outputs><Output key="1" name="DestinationID"/></Outputs><Configuration><DefinedProcessProperty componentId="{pp_id}" componentName="{pp_name}" propertyKey="346725d9-ae91-4b20-b0b8-76051ef2c63c" propertyName="DestinationID"/></Configuration></FunctionStep>
    <FunctionStep cacheEnabled="true" cacheOption="none" category="ProcessProperty" enabled="true" key="2" name="Get Process Property" position="2" sumEnabled="false" type="DefinedProcessPropertyGet" x="30.0" y="82.0"><Inputs/><Outputs><Output key="1" name="SenderID"/></Outputs><Configuration><DefinedProcessProperty componentId="{pp_id}" componentName="{pp_name}" propertyKey="4581226a-338b-4ee8-83a2-c4a602ca37cd" propertyName="SenderID"/></Configuration></FunctionStep>
    <FunctionStep cacheEnabled="true" cacheOption="none" category="ProcessProperty" enabled="true" key="3" name="Get Process Property" position="3" sumEnabled="false" type="DefinedProcessPropertyGet" x="30.0" y="154.0"><Inputs/><Outputs><Output key="1" name="OperationOrganizationID"/></Outputs><Configuration><DefinedProcessProperty componentId="{pp_id}" componentName="{pp_name}" propertyKey="87d4f770-3060-4aa0-8550-bc5ef83578c9" propertyName="OperationOrganizationID"/></Configuration></FunctionStep>
    <FunctionStep cacheEnabled="true" cacheOption="none" category="ProcessProperty" enabled="true" key="4" name="Get Process Property" position="4" sumEnabled="false" type="DefinedProcessPropertyGet" x="30.0" y="226.0"><Inputs/><Outputs><Output key="1" name="MessageType"/></Outputs><Configuration><DefinedProcessProperty componentId="{pp_id}" componentName="{pp_name}" propertyKey="eac70b0d-3b93-4685-9324-54e2e642352d" propertyName="MessageType"/></Configuration></FunctionStep>
    <FunctionStep cacheEnabled="true" cacheOption="none" category="ProcessProperty" enabled="true" key="5" name="Get Process Property" position="5" sumEnabled="false" type="DefinedProcessPropertyGet" x="30.0" y="298.0"><Inputs/><Outputs><Output key="1" name="RebateIndicator"/></Outputs><Configuration><DefinedProcessProperty componentId="{pp_id}" componentName="{pp_name}" propertyKey="95274e69-53a8-45dd-a3cb-e24389eb217f" propertyName="RebateIndicator"/></Configuration></FunctionStep>
    <FunctionStep category="userdefined" id="{mapfn_id}" key="10" name="CurDate_to_YYYYMMDD" position="10" type="userdefined" x="30.0" y="650.0"><Inputs><Input key="1" name="A"/></Inputs><Outputs><Output key="1" name="B"/><Output key="2" name="C"/></Outputs><Configuration/></FunctionStep>
    <FunctionStep cacheEnabled="true" cacheOption="none" category="ProcessProperty" enabled="true" key="11" name="Get Process Property" position="11" sumEnabled="false" type="DefinedProcessPropertyGet" x="30.0" y="771.0"><Inputs/><Outputs><Output key="1" name="InitialChange"/></Outputs><Configuration><DefinedProcessProperty componentId="{pp_id}" componentName="{pp_name}" propertyKey="f44dac41-ffa5-4d65-a3a4-0561b67448cf" propertyName="InitialChange"/></Configuration></FunctionStep>
    <FunctionStep cacheEnabled="true" cacheOption="none" category="ProcessProperty" enabled="true" key="12" name="Get Process Property" position="12" sumEnabled="false" type="DefinedProcessPropertyGet" x="30.0" y="843.0"><Inputs/><Outputs><Output key="1" name="CustomerEntryType"/></Outputs><Configuration><DefinedProcessProperty componentId="{pp_id}" componentName="{pp_name}" propertyKey="dcb5c357-caca-471d-9035-58f7398403fc" propertyName="CustomerEntryType"/></Configuration></FunctionStep>
  </Functions>
  <Defaults/><DocumentCacheJoins/>
</Map>"""
    return wrap_component(name, "transform.map", inner, folder_id)


def build_mq_connector(manifest, folder_id=""):
    mq = manifest["mq"]
    inner = f"""
<GenericConnectionConfig>
  <field id="version" type="string" value="V2_0"/>
  <field id="server_type" type="string" value="{mq['server_type']}"/>
  <field id="authentication" type="boolean" value="false"/>
  <field id="username" type="string" value=""/>
  <field id="password" type="password" value=""/>
  <field id="jndi_lookup_factory" type="string" value=""/>
  <field id="initial_context_factory" type="string" value=""/>
  <field id="provider_url" type="string" value=""/>
  <field id="jdbc_url" type="string" value=""/>
  <field id="jms_properties" type="customproperties"><customProperties/></field>
  <field id="websphere_host_name" type="string" value=""/>
  <field id="websphere_host_list" type="string" value="{mq['host_list']}"/>
  <field id="websphere_host_port" type="integer" value=""/>
  <field id="websphere_queue_manager" type="string" value="{mq['queue_manager']}"/>
  <field id="websphere_channel" type="string" value="{mq['channel']}"/>
  <field id="websphere_use_ssl" type="boolean" value="{str(mq['use_ssl']).lower()}"/>
  <field id="websphere_ssl_suite_option" type="string" value="{mq['ssl_cipher']}"/>
  <field id="websphere_ssl_suite_text" type="string" value=""/>
  <field id="use_connection_pooling" type="boolean" value="false"/>
  <field id="pool_maximum_connections" type="integer" value=""/>
  <field id="pool_minimum_connections" type="integer" value=""/>
  <field id="pool_maximum_idle_time" type="integer" value=""/>
  <field id="pool_maximum_wait_time" type="integer" value=""/>
  <field id="pool_exhausted_action" type="string" value=""/>
</GenericConnectionConfig>"""
    return wrap_component(mq["connector_name"], "connector-settings", inner, folder_id, sub="officialboomi-X3979C-jmsv2-prod")


def build_mq_operation(manifest, folder_id=""):
    mq = manifest["mq"]
    inner = f"""
<Operation returnApplicationErrors="false" trackResponse="false">
  <Archiving directory="" enabled="false"/>
  <Configuration>
    <GenericOperationConfig customOperationType="SEND" objectTypeId="dynamic_destination" objectTypeName="Dynamic Destination" operationType="CREATE" requestProfileType="binary" responseProfileType="json">
      <field id="use_transaction" type="boolean" value="false"/>
      <field id="time_to_live" type="integer" value="0"/>
      <field id="jms_operation_properties" type="customproperties"><customProperties/></field>
      <field id="destination" type="string" value="{mq['destination_queue']}"/>
      <field id="destination_type" type="string" value="{mq['destination_type']}"/>
      <dynamicOperationField displayType="list" id="destination" label="Destination" overrideable="true" type="string"><helpText>Destination where messages will be sent.</helpText></dynamicOperationField>
      <dynamicOperationField displayType="list" id="destination_type" label="Destination Type" overrideable="true" type="string"><defaultValue>text_message</defaultValue><allowedValue label="Text Message"><value>text_message</value></allowedValue><allowedValue label="Byte Message"><value>byte_message</value></allowedValue></dynamicOperationField>
      <Options><QueryOptions><Fields><ConnectorObject name="Dynamic Destination"><FieldList><ConnectorField filterable="true" name="destination" selectable="true" selected="true" sortable="true"/><ConnectorField filterable="true" name="destinationType" selectable="true" selected="true" sortable="true"/></FieldList></ConnectorObject></Fields><Inputs/></QueryOptions></Options>
    </GenericOperationConfig>
  </Configuration>
  <Tracking><TrackedFields/></Tracking><Caching/>
</Operation>"""
    return wrap_component(mq["operation_name"], "connector-action", inner, folder_id, sub="officialboomi-X3979C-jmsv2-prod")


def build_axway_connector(manifest, folder_id=""):
    s = manifest["sftp"]
    inner = f"""
<GenericConnectionConfig>
  <field id="remoteDirectory" type="string" value="{s['remote_directory']}"/>
  <field id="host" type="string" value="{s['host']}"/>
  <field id="port" type="integer" value="{s['port']}"/>
  <field id="username" type="string" value="{s['username']}"/>
  <field id="password" type="password" value=""/>
  <field id="authType" type="string" value="{s['auth_type']}"/>
  <field id="keyPath" type="string" value="{s['key_path']}"/>
  <field id="keyPswrd" type="password" value=""/>
  <field id="prvkeyContent" type="password" value=""/>
  <field id="keyContentPwd" type="password" value=""/>
  <field id="pubkeyContent" type="password" value=""/>
  <field id="keyPairName" type="string" value=""/>
  <field id="enablePooling" type="boolean" value="false"/>
  <field id="proxyEnable" type="boolean" value="false"/>
  <field id="proxyType" type="string" value=""/>
  <field id="proxyHost" type="string" value=""/>
  <field id="proxyPort" type="integer" value=""/>
  <field id="proxyuserName" type="string" value=""/>
  <field id="proxyPassword" type="password" value=""/>
  <field id="kex" type="string" value="curve25519-sha256,curve25519-sha256@libssh.org,ecdh-sha2-nistp256,ecdh-sha2-nistp384,ecdh-sha2-nistp521,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512,diffie-hellman-group14-sha256"/>
  <field id="server_host_key" type="string" value="ssh-ed25519,ecdsa-sha2-nistp256,ecdsa-sha2-nistp384,ecdsa-sha2-nistp521,rsa-sha2-512,rsa-sha2-256"/>
  <field id="cipher.s2c" type="string" value="aes128-ctr,aes192-ctr,aes256-ctr,aes128-gcm@openssh.com,aes256-gcm@openssh.com"/>
  <field id="cipher.c2s" type="string" value="aes128-ctr,aes192-ctr,aes256-ctr,aes128-gcm@openssh.com,aes256-gcm@openssh.com"/>
  <field id="mac.s2c" type="string" value="hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,hmac-sha1-etm@openssh.com,hmac-sha2-256,hmac-sha2-512,hmac-sha1"/>
  <field id="mac.c2s" type="string" value="hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,hmac-sha1-etm@openssh.com,hmac-sha2-256,hmac-sha2-512,hmac-sha1"/>
  <field id="compression.s2c" type="string" value="none"/>
  <field id="compression.c2s" type="string" value="none"/>
  <field id="sftpCustomConfiguration" type="customproperties"><customProperties/></field>
</GenericConnectionConfig>"""
    return wrap_component(s["connector_name"], "connector-settings", inner, folder_id, sub="officialboomi-X3979C-sftpvx-prod")


def build_sftp_operation(manifest, folder_id=""):
    s = manifest["sftp"]
    inner = f"""
<Operation returnApplicationErrors="false" trackResponse="true">
  <Archiving directory="" enabled="false"/>
  <Configuration>
    <GenericOperationConfig customOperationType="READ" objectTypeId="file" objectTypeName="File" operationType="GET" requestProfileType="xml" responseProfileType="binary">
      <field id="actionAfterRead" type="string" value="{s['action_after_read']}"/>
      <field id="destination" type="string" value=""/>
      <field id="newFileName" type="string" value=""/>
      <Options><QueryOptions><Fields><ConnectorObject name="File"><FieldList/></ConnectorObject></Fields><Inputs><Input key="0" name="ID"/></Inputs></QueryOptions></Options>
    </GenericOperationConfig>
  </Configuration>
  <Tracking><TrackedFields/></Tracking><Caching/>
</Operation>"""
    return wrap_component(s["operation_name"], "connector-action", inner, folder_id, sub="officialboomi-X3979C-sftpvx-prod")


def build_subprocess_sftp(manifest, folder_id, ax_conn_id, ax_op_id, src_id):
    name = manifest["subprocesses"]["sftp_subprocess_name"]
    filename = manifest["sftp"]["read_file_name"]
    inner = f"""
<process allowSimultaneous="false" enableUserLog="false" processLogOnErrorOnly="false" purgeDataImmediately="false" stopProcessingIfZeroDocuments="true" updateRunDates="false" workload="general">
  <shapes>
    <shape image="start" name="shape1" shapetype="start" userlabel="Pass Thru" x="48.0" y="46.0"><configuration><noaction/></configuration><dragpoints><dragpoint name="shape1.dragpoint1" toShape="shape4" x="224.0" y="56.0"/></dragpoint></dragpoints></shape>
    <shape image="returndocuments_icon" name="shape3" shapetype="returndocuments" userlabel="Return" x="816.0" y="48.0"><configuration><returndocuments label="Return"/></configuration><dragpoints/></shape>
    <shape image="catcherrors_icon" name="shape4" shapetype="catcherrors" userlabel="Try/Catch" x="240.0" y="48.0"><configuration><catcherrors catchAll="true" retryCount="2"/></configuration><dragpoints><dragpoint identifier="default" name="shape4.dragpoint1" text="Try" toShape="shape8" x="432.0" y="56.0"/><dragpoint identifier="error" name="shape4.dragpoint2" text="Catch" toShape="shape6" x="416.0" y="216.0"/></dragpoints></shape>
    <shape image="exception_icon" name="shape5" shapetype="exception" userlabel="Exception" x="624.0" y="208.0"><configuration><exception stopProcessReturnSingleDoc="false" stopsingledoc="false" title=""><exMessage>{{1}}</exMessage><exParameters><parametervalue key="0" usesEncryption="false" valueType="track"><trackparameter defaultValue="" propertyId="meta.base.catcherrorsmessage" propertyName="Base - Try/Catch Message"/></parametervalue></exParameters></exception></configuration><dragpoints/></shape>
    <shape image="documentproperties_icon" name="shape6" shapetype="documentproperties" userlabel="capture payload" x="432.0" y="208.0"><configuration><documentproperties><documentproperty defaultValue="" isDynamicCredential="false" isTradingPartner="false" name="Dynamic Process Property - DPP_CM_DATA" persist="false" propertyId="process.DPP_CM_DATA" shouldEncrypt="false"><sourcevalues><parametervalue key="1" usesEncryption="false" valueType="current"/></sourcevalues></documentproperty></documentproperties></configuration><dragpoints><dragpoint name="shape6.dragpoint1" toShape="shape5" x="608.0" y="216.0"/></dragpoints></shape>
    <shape image="documentproperties_icon" name="shape7" shapetype="documentproperties" userlabel="" x="624.0" y="48.0"><configuration><documentproperties><documentproperty defaultValue="" isDynamicCredential="false" isTradingPartner="false" name="Dynamic Document Property - DDP_CORRELATION_ID" persist="false" propertyId="dynamicdocument.DDP_CORRELATION_ID" shouldEncrypt="false"><sourcevalues><parametervalue key="1" usesEncryption="false" valueType="profile"><profileelement elementId="70" elementName="UUID (Statement/Fields/UUID)" profileId="{src_id}" profileType="profile.db"/></parametervalue></sourcevalues></documentproperty></documentproperties></configuration><dragpoints><dragpoint name="shape7.dragpoint1" toShape="shape3" x="800.0" y="56.0"/></dragpoints></shape>
    <shape image="connectoraction_icon" name="shape8" shapetype="connectoraction" userlabel="" x="448.0" y="48.0"><configuration><connectoraction actionType="Read" allowDynamicCredentials="NONE" connectionId="{ax_conn_id}" connectorType="officialboomi-X3979C-sftpvx-prod" hideSettings="false" operationId="{ax_op_id}" parameter-profile="EMBEDDED|genericparameterchooser|{ax_op_id}"><parameters><parametervalue elementToSetId="0" elementToSetName="ID" name="ID" usesEncryption="false" valueType="static"><staticparameter staticproperty="{filename}"/></parametervalue></parameters><dynamicProperties/></connectoraction></configuration><dragpoints><dragpoint name="shape8.dragpoint1" toShape="shape7" x="608.0" y="56.0"/></dragpoints></shape>
  </shapes>
</process>"""
    return wrap_component(name, "process", inner, folder_id)


def build_subprocess_mq(manifest, folder_id, mq_conn_id, mq_op_id):
    name = manifest["subprocesses"]["mq_subprocess_name"]
    inner = f"""
<process allowSimultaneous="false" enableUserLog="false" processLogOnErrorOnly="false" purgeDataImmediately="false" stopProcessingIfZeroDocuments="true" updateRunDates="false" workload="general">
  <shapes>
    <shape image="start" name="shape1" shapetype="start" userlabel="PassThru" x="48.0" y="46.0"><configuration><passthroughaction/></configuration><dragpoints><dragpoint name="shape1.dragpoint1" toShape="shape4" x="224.0" y="56.0"/></dragpoints></shape>
    <shape image="connectoraction_icon" name="shape2" shapetype="connectoraction" userlabel="" x="816.0" y="48.0"><configuration><connectoraction actionType="SEND" allowDynamicCredentials="NONE" connectionId="{mq_conn_id}" connectorType="officialboomi-X3979C-jmsv2-prod" hideSettings="false" operationId="{mq_op_id}"><parameters/><dynamicProperties/></connectoraction></configuration><dragpoints><dragpoint name="shape2.dragpoint1" toShape="shape3" x="992.0" y="56.0"/></dragpoints></shape>
    <shape image="stop_icon" name="shape3" shapetype="stop" userlabel="" x="1008.0" y="48.0"><configuration><stop continue="true"/></configuration><dragpoints/></shape>
    <shape image="catcherrors_icon" name="shape4" shapetype="catcherrors" userlabel="Try/Catch" x="240.0" y="48.0"><configuration><catcherrors catchAll="true" retryCount="2"/></configuration><dragpoints><dragpoint identifier="default" name="shape4.dragpoint1" text="Try" toShape="shape8" x="608.0" y="56.0"/><dragpoint identifier="error" name="shape4.dragpoint2" text="Catch" toShape="shape6" x="416.0" y="216.0"/></dragpoints></shape>
    <shape image="exception_icon" name="shape5" shapetype="exception" userlabel="Exception" x="624.0" y="208.0"><configuration><exception stopProcessReturnSingleDoc="false" stopsingledoc="true" title=""><exMessage>{{1}}</exMessage><exParameters><parametervalue key="0" usesEncryption="false" valueType="track"><trackparameter defaultValue="" propertyId="meta.base.catcherrorsmessage" propertyName="Base - Try/Catch Message"/></parametervalue></exParameters></exception></configuration><dragpoints/></shape>
    <shape image="documentproperties_icon" name="shape6" shapetype="documentproperties" userlabel="capture payload" x="432.0" y="208.0"><configuration><documentproperties><documentproperty defaultValue="" isDynamicCredential="false" isTradingPartner="false" name="Dynamic Process Property - DPP_CM_DATA" persist="false" propertyId="process.DPP_CM_DATA" shouldEncrypt="false"><sourcevalues><parametervalue key="1" usesEncryption="false" valueType="current"/></sourcevalues></documentproperty></documentproperties></configuration><dragpoints><dragpoint name="shape6.dragpoint1" toShape="shape5" x="608.0" y="216.0"/></dragpoints></shape>
    <shape image="notify_icon" name="shape8" shapetype="notify" userlabel="" x="624.0" y="48.0"><configuration><notify disableEvent="true" enableUserLog="false" perExecution="false" title=""><notifyMessage>{{1}}</notifyMessage><notifyMessageLevel>INFO</notifyMessageLevel><notifyParameters><parametervalue key="0" usesEncryption="false" valueType="track"><trackparameter defaultValue="" propertyId="dynamicdocument.DDP_CORRELATION_ID" propertyName="Dynamic Document Property - DDP_CORRELATION_ID"/></parametervalue></notifyParameters></notify></configuration><dragpoints><dragpoint name="shape8.dragpoint1" toShape="shape2" x="800.0" y="56.0"/></dragpoints></shape>
  </shapes>
</process>"""
    return wrap_component(name, "process", inner, folder_id)


def build_main_process(manifest, folder_id, sub_sftp_id, map_id, sub_mq_id):
    name = manifest["pattern"]["name"]
    desc = manifest["pattern"].get("description", "")
    inner = f"""
<process allowSimultaneous="false" enableUserLog="false" processLogOnErrorOnly="false" purgeDataImmediately="false" stopProcessingIfZeroDocuments="true" updateRunDates="true" workload="general">
  <shapes>
    <shape image="start" name="shape1" shapetype="start" userlabel="start" x="48.0" y="46.0"><configuration><noaction/></configuration><dragpoints><dragpoint name="shape1.dragpoint1" toShape="shape7" x="224.0" y="56.0"/></dragpoints></shape>
    <shape image="map_icon" name="shape5" shapetype="map" userlabel="" x="624.0" y="48.0"><configuration><map mapId="{map_id}"/></configuration><dragpoints><dragpoint name="shape5.dragpoint1" toShape="shape17" x="800.0" y="56.0"/></dragpoints></shape>
    <shape image="catcherrors_icon" name="shape7" shapetype="catcherrors" userlabel="Global Try/catch" x="240.0" y="48.0"><configuration><catcherrors catchAll="true" retryCount="0"/></configuration><dragpoints><dragpoint identifier="default" name="shape7.dragpoint1" text="Try" toShape="shape14" x="416.0" y="56.0"/><dragpoint identifier="error" name="shape7.dragpoint2" text="Catch" toShape="shape18" x="448.0" y="232.0"/></dragpoints></shape>
    <shape image="processcall_icon" name="shape14" shapetype="processcall" userlabel="" x="432.0" y="48.0"><configuration><processcall abort="true" processId="{sub_sftp_id}" wait="true"><parameters/><returnpaths><returnpaths childShapeName="shape3" returnLabel="Return"/></returnpaths></processcall></configuration><dragpoints><dragpoint identifier="shape3" name="shape14.dragpoint1" text="Return" toShape="shape5" x="608.0" y="56.0"/></dragpoints></shape>
    <shape image="processcall_icon" name="shape17" shapetype="processcall" userlabel="" x="816.0" y="48.0"><configuration><processcall abort="true" processId="{sub_mq_id}" wait="true"><parameters/><returnpaths/></processcall></configuration><dragpoints/></shape>
    <shape image="stop_icon" name="shape18" shapetype="stop" userlabel="stop" x="464.0" y="224.0"><configuration><stop continue="true"/></configuration><dragpoints/></shape>
  </shapes>
</process>"""
    return wrap_component(name, "process", inner, folder_id, desc=desc)


def build_component_inventory(ids):
    rows = []
    for label, entry in ids.items():
        rows.append({
            "ComponentType": entry["type"],
            "ComponentName": label,
            "ComponentID": entry["id"],
            "Reuse": str(entry.get("reuse", False)).lower(),
            "Notes": entry.get("notes", ""),
        })
    return rows


def run(manifest_path, csv_path=None, existing_ids_path=None, dry_run=False):
    manifest = load_manifest(manifest_path)
    client = BoomiClient()
    existing_ids = load_existing_ids(existing_ids_path)

    folder_id = manifest["pattern"].get("folder_id", "") or ""
    created = {}

    print("\nBoomi manifest automation starting")
    print(f"Manifest: {manifest_path}")
    print(f"Dry run: {dry_run}")
    print(f"Folder: {'root' if not folder_id else folder_id}")
    if existing_ids_path:
        print(f"Existing IDs: {existing_ids_path}")
    print()

    def resolve_existing_id(label, manifest_existing=None):
        return manifest_existing or existing_ids.get(label)

    pp_id = client.create_or_reuse(
        manifest["process_properties"]["name"],
        build_process_property(manifest, folder_id),
        existing_id=resolve_existing_id(manifest["process_properties"]["name"]),
        dry_run=dry_run,
    )
    created[manifest["process_properties"]["name"]] = {"type": "processproperty", "id": pp_id, "notes": "Process property group"}

    mapfn_id = client.create_or_reuse(
        manifest["map_function"]["name"],
        build_map_function(manifest, folder_id),
        dry_run=dry_run,
    )
    created[manifest["map_function"]["name"]] = {"type": "transform.function", "id": mapfn_id, "notes": "Re-usable map function"}

    tgt_id = client.create_or_reuse(
        manifest["target_profile"]["name"],
        build_target_profile(manifest, folder_id),
        dry_run=dry_run,
    )
    created[manifest["target_profile"]["name"]] = {"type": "profile.xml", "id": tgt_id, "notes": "Target XML schema"}

    src_id = client.create_or_reuse(
        manifest["source_profile"]["name"],
        build_source_profile(manifest, folder_id),
        dry_run=dry_run,
    )
    created[manifest["source_profile"]["name"]] = {"type": "profile.db", "id": src_id, "notes": "Database source schema"}

    map_id = client.create_or_reuse(
        manifest["map"]["name"],
        build_map(manifest, folder_id, pp_id, src_id, tgt_id, mapfn_id),
        dry_run=dry_run,
    )
    created[manifest["map"]["name"]] = {"type": "transform.map", "id": map_id, "notes": "Data mapping"}

    if manifest["mq"].get("reuse") and manifest["mq"].get("existing_connector_id"):
        mq_conn_id = manifest["mq"]["existing_connector_id"]
        created[manifest["mq"]["connector_name"]] = {"type": "connector-settings", "id": mq_conn_id, "reuse": True, "notes": "Existing MQ connector reused"}
        print(f"  -> {manifest['mq']['connector_name']} [REUSE] {mq_conn_id}")
    else:
        mq_conn_id = client.create_or_reuse(
            manifest["mq"]["connector_name"],
            build_mq_connector(manifest, folder_id),
            existing_id=resolve_existing_id(manifest["mq"]["connector_name"]),
            dry_run=dry_run,
        )
        created[manifest["mq"]["connector_name"]] = {"type": "connector-settings", "id": mq_conn_id, "notes": "MQ connector"}

    mq_op_id = client.create_or_reuse(
        manifest["mq"]["operation_name"],
        build_mq_operation(manifest, folder_id),
        dry_run=dry_run,
    )
    created[manifest["mq"]["operation_name"]] = {"type": "connector-action", "id": mq_op_id, "notes": "MQ operation"}

    if manifest["sftp"].get("reuse") and manifest["sftp"].get("existing_connector_id"):
        ax_conn_id = manifest["sftp"]["existing_connector_id"]
        created[manifest["sftp"]["connector_name"]] = {"type": "connector-settings", "id": ax_conn_id, "reuse": True, "notes": "Existing SFTP connector reused"}
        print(f"  -> {manifest['sftp']['connector_name']} [REUSE] {ax_conn_id}")
    else:
        ax_conn_id = client.create_or_reuse(
            manifest["sftp"]["connector_name"],
            build_axway_connector(manifest, folder_id),
            existing_id=resolve_existing_id(manifest["sftp"]["connector_name"]),
            dry_run=dry_run,
        )
        created[manifest["sftp"]["connector_name"]] = {"type": "connector-settings", "id": ax_conn_id, "notes": "SFTP connector"}

    ax_op_id = client.create_or_reuse(
        manifest["sftp"]["operation_name"],
        build_sftp_operation(manifest, folder_id),
        dry_run=dry_run,
    )
    created[manifest["sftp"]["operation_name"]] = {"type": "connector-action", "id": ax_op_id, "notes": "SFTP operation"}

    sub_sftp_id = client.create_or_reuse(
        manifest["subprocesses"]["sftp_subprocess_name"],
        build_subprocess_sftp(manifest, folder_id, ax_conn_id, ax_op_id, src_id),
        dry_run=dry_run,
    )
    created[manifest["subprocesses"]["sftp_subprocess_name"]] = {"type": "process", "id": sub_sftp_id, "notes": "SFTP subprocess"}

    sub_mq_id = client.create_or_reuse(
        manifest["subprocesses"]["mq_subprocess_name"],
        build_subprocess_mq(manifest, folder_id, mq_conn_id, mq_op_id),
        dry_run=dry_run,
    )
    created[manifest["subprocesses"]["mq_subprocess_name"]] = {"type": "process", "id": sub_mq_id, "notes": "MQ subprocess"}

    main_id = client.create_or_reuse(
        manifest["pattern"]["name"],
        build_main_process(manifest, folder_id, sub_sftp_id, map_id, sub_mq_id),
        dry_run=dry_run,
    )
    created[manifest["pattern"]["name"]] = {"type": "process", "id": main_id, "notes": "Main orchestration process"}

    if csv_path:
        client.save_ids_csv(build_component_inventory(created), csv_path)
        print(f"\nSaved component inventory to {csv_path}")

    print("\nComponent summary:")
    for label, entry in created.items():
        print(f"  {label:<45} {entry['type']:<18} {entry['id']} {('[reuse]' if entry.get('reuse') else '')}")


def parse_args(args):
    manifest = None
    csv_path = None
    existing_ids_path = None
    dry_run = False

    i = 1
    while i < len(args):
        arg = args[i]
        if arg == "--csv" and i + 1 < len(args):
            csv_path = args[i + 1]
            i += 2
        elif arg == "--load-ids" and i + 1 < len(args):
            existing_ids_path = args[i + 1]
            i += 2
        elif arg == "--dry-run":
            dry_run = True
            i += 1
        elif not manifest:
            manifest = arg
            i += 1
        else:
            raise SystemExit("Usage: python boomi.py manifest.yaml --csv output.csv [--load-ids existing_ids.csv] [--dry-run]")

    if not manifest:
        raise SystemExit("Usage: python boomi.py manifest.yaml --csv output.csv [--load-ids existing_ids.csv] [--dry-run]")
    return manifest, csv_path, existing_ids_path, dry_run


if __name__ == "__main__":
    manifest_path, csv_path, existing_ids_path, dry_run = parse_args(sys.argv)
    run(manifest_path, csv_path=csv_path, existing_ids_path=existing_ids_path, dry_run=dry_run)
