<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:output encoding="utf-8"/>
    <xsl:param name="DEV_BUCKET_PREFIX"/>

    <xsl:template match="/">
        <html>
            <head>
                <title>Case docket:
                    <xsl:value-of
                            select="gov_uscourts_docket/case_details/case_name"/>
                </title>
            </head>

            <style>
                table {
                  border: 1px black solid;
                  margin: 0 0 0 50px;
                  border-collapse: collapse;
                }

                td {
                  border: 1px black solid;
                  padding: 1px 30px 1px 10px;
                }
            </style>

            <body>

                <xsl:apply-templates
                        select="gov_uscourts_docket/case_details"/>
                <xsl:apply-templates
                        select="gov_uscourts_docket/party_list"/>
                <xsl:apply-templates
                        select="gov_uscourts_docket/document_list"/>

            </body>
        </html>
    </xsl:template>

    <!-- Start matching rules for case details-->
    <xsl:template match="gov_uscourts_docket/case_details">
        <h2>Case details</h2>
        <table>
            <xsl:apply-templates/>
        </table>
    </xsl:template>

    <xsl:template match="gov_uscourts_docket/case_details/court">
        <tr>
            <td>
                <b>Court:</b>
            </td>
            <td>
                <xsl:value-of select="."/>
            </td>
        </tr>
    </xsl:template>

    <xsl:template match="gov_uscourts_docket/case_details/case_name">
        <tr>
            <td>
                <b>Case Name:</b>
            </td>
            <td>
                <xsl:value-of select="."/>
            </td>
        </tr>
    </xsl:template>

    <xsl:template match="gov_uscourts_docket/case_details/docket_num">
        <tr>
            <td>
                <b>Docket #:</b>
            </td>
            <td>
                <xsl:value-of select="."/>
            </td>
        </tr>
    </xsl:template>

    <xsl:template match="gov_uscourts_docket/case_details/pacer_case_num">
        <tr>
            <td>
                <b>PACER case #:</b>
            </td>
            <td>
                <xsl:value-of select="."/>
            </td>
        </tr>
    </xsl:template>

    <xsl:template match="gov_uscourts_docket/case_details/date_case_filed">
        <tr>
            <td>
                <b>Date filed:</b>
            </td>
            <td>
                <xsl:value-of select="."/>
            </td>
        </tr>
    </xsl:template>

    <xsl:template
            match="gov_uscourts_docket/case_details/date_case_terminated">
        <tr>
            <td>
                <b>Date terminated:</b>
            </td>
            <td>
                <xsl:value-of select="."/>
            </td>
        </tr>
    </xsl:template>

    <xsl:template match="gov_uscourts_docket/case_details/date_last_filing">
        <tr>
            <td>
                <b>Date of last filing:</b>
            </td>
            <td>
                <xsl:value-of select="."/>
            </td>
        </tr>
    </xsl:template>

    <xsl:template match="gov_uscourts_docket/case_details/assigned_to">
        <tr>
            <td>
                <b>Assigned to:</b>
            </td>
            <td>
                <xsl:value-of select="."/>
            </td>
        </tr>
    </xsl:template>


    <xsl:template match="gov_uscourts_docket/case_details/referred_to">
        <tr>
            <td>
                <b>Referred to:</b>
            </td>
            <td>
                <xsl:value-of select="."/>
            </td>
        </tr>
    </xsl:template>

    <xsl:template match="gov_uscourts_docket/case_details/case_cause">
        <tr>
            <td>
                <b>Case Cause:</b>
            </td>
            <td>
                <xsl:value-of select="."/>
            </td>
        </tr>
    </xsl:template>

    <xsl:template match="gov_uscourts_docket/case_details/nature_of_suit">
        <tr>
            <td>
                <b>Nature of Suit:</b>
            </td>
            <td>
                <xsl:value-of select="."/>
            </td>
        </tr>
    </xsl:template>

    <xsl:template match="gov_uscourts_docket/case_details/jury_demand">
        <tr>
            <td>
                <b>Jury Demand:</b>
            </td>
            <td>
                <xsl:value-of select="."/>
            </td>
        </tr>
    </xsl:template>

    <xsl:template match="gov_uscourts_docket/case_details/jurisdiction">
        <tr>
            <td>
                <b>Jurisdiction:</b>
            </td>
            <td>
                <xsl:value-of select="."/>
            </td>
        </tr>
    </xsl:template>

    <xsl:template match="gov_uscourts_docket/case_details/demand">
        <tr>
            <td>
                <b>Demand:</b>
            </td>
            <td>
                <xsl:value-of select="."/>
            </td>
        </tr>
    </xsl:template>

    <!-- End matching rules for case details-->

    <!-- Start matching rules for attorneys-->

    <xsl:template match="gov_uscourts_docket/party_list">
        <h2>Parties</h2>

        <table>
            <tr>
                <td>
                    <b>Represented Party</b>
                </td>
                <td>
                    <b>Attorney &amp; Contact Info</b>
                </td>
            </tr>

            <xsl:apply-templates select="party">
                <xsl:apply-templates/>
            </xsl:apply-templates>
        </table>

    </xsl:template>

    <xsl:template match="gov_uscourts_docket/party_list/party">
        <tr>
            <td>
                <xsl:value-of select="name"/>
                <br/>
                <xsl:value-of select="type"/>
                <br/>
                <xsl:value-of select="extra_info"/>
            </td>
            <td>
                <xsl:apply-templates select="attorney_list"/>
            </td>
        </tr>
    </xsl:template>

    <xsl:template match="gov_uscourts_docket/party_list/party/attorney_list">
        <xsl:apply-templates select="attorney">
            <xsl:apply-templates/>>
        </xsl:apply-templates>
    </xsl:template>

    <xsl:template
            match="gov_uscourts_docket/party_list/party/attorney_list/attorney">
        <pre>
            <xsl:value-of select="attorney_name"/>
            <br/>
            <xsl:value-of select="contact"/>
            <br/>
            <i>
                <xsl:value-of select="attorney_role"/>
            </i>
        </pre>
        <br/>
    </xsl:template>
    <!-- End matching rules for attorneys-->

    <!-- Start matching rules for case documents-->

    <xsl:template match="gov_uscourts_docket/document_list">

        <h2>Documents</h2>

        <table>
            <tr>
                <td>
                    <b>Date Filed</b>
                </td>
                <td>
                    <b>Document #</b>
                </td>
                <td>
                    <b>Attachment #</b>
                </td>
                <td>
                    <b>Short Description</b>
                </td>
                <td>
                    <b>Long Description</b>
                </td>
                <td>
                    <b>Upload date</b>
                </td>
                <td>
                    <b>SHA1 hash</b>
                </td>
            </tr>

            <xsl:apply-templates select="document">
                <xsl:sort select="@doc_num" data-type="number"/>
                <xsl:sort select="@attachment_num" data-type="number"/>
            </xsl:apply-templates>
        </table>

    </xsl:template>

    <xsl:template match="gov_uscourts_docket/document_list/document">
        <tr>
            <td>
                <xsl:value-of select="date_filed"/>
            </td>
            <xsl:apply-templates select="." mode="availability"/>
            <td>
                <xsl:value-of select="@attachment_num"/>
            </td>
            <td>
                <xsl:value-of select="short_desc"/>
            </td>
            <td>
                <xsl:value-of select="long_desc"/>
            </td>
            <td>
                <xsl:value-of select="upload_date"/>
            </td>
            <td>
                <xsl:value-of select="sha1"/>
            </td>
        </tr>
    </xsl:template>

    <xsl:template
            match="gov_uscourts_docket/document_list/document[available='1']"
            mode="availability">
        <td>
            <!--
              Make the anchor element using the DEV_BUCKET_PREFIX value.
              The choose statement is needed here so we can be sure to add
              the period after DEV_BUCKET_PREFIX if necessary.
            -->
            <xsl:choose>
                <xsl:when test="string-length($DEV_BUCKET_PREFIX) > 0">
                    <xsl:element name="a">
                        <xsl:attribute name="href">
                            <xsl:value-of select="concat(
                              'http://www.archive.org/download/',
                              $DEV_BUCKET_PREFIX,
                              '.',
                              'gov.uscourts.{../../case_details/court}.',
                              '{../../case_details/pacer_case_num}/',
                              'gov.uscourts.{../../case_details/court}.',
                              '{../../case_details/pacer_case_num}.',
                              '{@doc_num}.{@attachment_num}.pdf')"/>
                        </xsl:attribute>
                        <xsl:value-of select="@doc_num"/>
                    </xsl:element>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Simple case, not a dev server-->
                    <a href="http://www.archive.org/download/gov.uscourts.{../../case_details/court}.{../../case_details/pacer_case_num}/gov.uscourts.{../../case_details/court}.{../../case_details/pacer_case_num}.{@doc_num}.{@attachment_num}.pdf">
                      <xsl:value-of select="@doc_num"/>
                  </a>
                </xsl:otherwise>
            </xsl:choose>

        </td>
    </xsl:template>

    <xsl:template
            match="gov_uscourts_docket/document_list/document[available='0']"
            mode="availability">
        <td>
            <xsl:value-of select="@doc_num"/>
        </td>
    </xsl:template>

    <xsl:template
            match="gov_uscourts_docket/document_list/document[count(available)=0]"
            mode="availability">
        <td>
            <xsl:value-of select="@doc_num"/>
        </td>
    </xsl:template>

    <!-- End matching rules for case documents-->

</xsl:stylesheet>
