import type { Feedback, Job } from '@/types';
import { FeedbackType } from '@/types';
import { stringifyError } from '@/utils/errors';
import { BugOutlined } from '@ant-design/icons';
import type { ButtonProps } from 'antd';
import { Button, Flex, Form, Input, message, Modal, Space } from 'antd';
import axios from 'axios';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export const JobIssueReportButton: React.FC<{
  job: Job;
  size?: ButtonProps['size'];
}> = ({ job, size }) => {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [messageApi, contextHolder] = message.useMessage();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values: {
    type: FeedbackType;
    subject: string;
    message: string;
  }) => {
    setLoading(true);
    try {
      const { data } = await axios.post<Feedback>('/api/feedback', {
        ...values,
        extra: {
          job_id: job.id,
          novel_id: job.extra.novel_id,
        },
      });
      messageApi.success('Feedback submitted successfully! Thank you.');
      form.resetFields();
      setOpen(false);
      navigate(`/feedback/${data.id}`);
    } catch (err) {
      messageApi.error(stringifyError(err, 'Failed to submit feedback'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {contextHolder}

      <Button
        danger
        size={size}
        type="default"
        icon={<BugOutlined />}
        onClick={() => setOpen(true)}
      >
        Report
      </Button>

      <Modal
        title={
          <Space>
            <BugOutlined /> Report Bug
          </Space>
        }
        open={open}
        onCancel={() => setOpen(false)}
        footer={null}
        width={600}
        destroyOnHidden
      >
        <Form
          form={form}
          size="large"
          layout="vertical"
          onFinish={handleSubmit}
          autoComplete="off"
          labelCol={{ style: { padding: 0 } }}
          initialValues={{
            type: FeedbackType.ISSUE,
            subject: `Job Failed: ${job.job_title || job.id}`,
            message: '',
          }}
        >
          <Form.Item name="type" hidden />
          <Form.Item
            name="subject"
            label="Subject"
            rules={[
              { required: true, message: 'Please enter a subject' },
              { max: 200, message: 'Subject must be less than 200 characters' },
            ]}
          >
            <Input
              placeholder="Brief description of your feedback"
              maxLength={200}
              showCount
            />
          </Form.Item>

          <Form.Item
            name="message"
            label="Message"
            rules={[
              {
                max: 5000,
                message: 'Message must be less than 5000 characters',
              },
            ]}
          >
            <Input.TextArea
              placeholder="You can optionally provide more details about the issue..."
              rows={3}
              maxLength={5000}
              showCount
            />
          </Form.Item>

          <Form.Item style={{ marginTop: 35 }}>
            <Flex justify="end" gap={10}>
              <Button onClick={() => setOpen(false)} disabled={loading}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit" loading={loading}>
                Submit
              </Button>
            </Flex>
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};
